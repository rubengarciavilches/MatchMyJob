import common
import my_types
from helper import fix_dict_str_or_none
from jobspy import scrape_jobs
import datetime
from supabase import create_client, Client

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
client = common.get_openai_client()

HOURS_OLD_NEW = 24
HOURS_OLD_UPDATE = 4


def scrape_and_store_jobs(search: my_types.JobSearchEntry, is_new_search=False):
    job_sources = [item.strip() for item in search['job_source'].split(',')]
    search_terms = [item.strip() for item in search['search_term'].split(',')]
    for job_source in job_sources:
        for search_term in search_terms:
            try:
                # Scrape jobs from LinkedIn
                jobs = scrape_jobs(
                    site_name=job_source,
                    search_term=search_term,
                    location=search['location'],
                    results_wanted=search['results_wanted'],
                    hours_old=HOURS_OLD_NEW if is_new_search else HOURS_OLD_UPDATE,
                    country_indeed=search['country'],  # Specific to Indeed
                    proxies=None,  # Add proxies if needed
                    linkedin_fetch_description=job_source == "linkedin",
                )

                # Store jobs in Supabase
                for job in jobs.to_dict("records"):
                    try:
                        job.pop('company_url_direct', None)
                        job.pop('company_addresses', None)
                        job.pop('company_industry', None)
                        job.pop('company_num_employees', None)
                        job.pop('company_revenue', None)
                        job.pop('company_description', None)
                        job.pop('banner_photo_url', None)
                        job.pop('ceo_name', None)
                        job.pop('ceo_photo_url', None)
                        if isinstance(job['date_posted'], datetime.datetime):
                            job['date_posted'] = job['date_posted'].strftime("%Y-%m-%d")
                        else:
                            job['date_posted'] = None
                        job['job_id'] = job.pop('id', None)
                        fix_dict_str_or_none(job)
                        existing_job = supabase.table('job').select('id').eq('job_url', job['job_url']).execute()
                        job['id'] = existing_job.data[0]['id'] if existing_job.data is not None else None
                        if existing_job.data:
                            logger.info(f"Job with URL {job['job_url']} already exists. Skipping insert.")
                        else:
                            # print(job)
                            response = supabase.table('job').insert(job, upsert=False).execute()
                            if not response.data:
                                logger.error(f"Error storing job: {response.error.message}")
                                continue
                            else:
                                logger.info("1")
                                job['id'] = response.data[0]['id']
                                logger.info(f"Stored job with ID: {response.data[0]['id']}")

                        search_job = {
                            'search_id': search['id'],
                            'job_id': job['id']
                        }
                        existing_job = (supabase.table('search_job')
                                        .select('search_id', 'job_id')
                                        .eq('search_id', search_job['search_id'])
                                        .eq('job_id', search_job['job_id'])
                                        .execute())
                        if existing_job.data:
                            continue
                        response = supabase.table('search_job').insert(search_job, upsert=False).execute()
                        if not response.data:
                            logger.error(f"Error storing job: {response.error.message}")
                        else:
                            logger.info("2")
                            logger.info(
                                f"Stored job with ID: <{response.data[0]['search_id']},{response.data[0]['job_id']}>")
                    except Exception as e:
                        logger.error(f"Error during job storing: {str(e)}")

            except Exception as e:
                logger.error(f"Error during job scraping: {str(e)}")
