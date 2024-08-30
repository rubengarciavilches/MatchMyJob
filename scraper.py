import common
from my_types import SearchJobEntry, SearchEntry
from helper import fix_dict_str_or_none
from jobspy import scrape_jobs
import datetime
from supabase import Client

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
client = common.get_openai_client()

HOURS_OLD_NEW = 24
HOURS_OLD_UPDATE = 4


def _format_job(job: SearchJobEntry) -> None:
    """
    Formats the job received from JobSpy to remove unnecessary fields and change the format of others to be ready to
    upload it.
    :param job: dictionary of values received from JobSpy
    :return: None
    """
    job.pop("company_url_direct", None)
    job.pop("company_addresses", None)
    job.pop("company_industry", None)
    job.pop("company_num_employees", None)
    job.pop("company_revenue", None)
    job.pop("company_description", None)
    job.pop("banner_photo_url", None)
    job.pop("ceo_name", None)
    job.pop("ceo_photo_url", None)
    if isinstance(job["date_posted"], datetime.datetime):
        job["date_posted"] = job["date_posted"].strftime("%Y-%m-%d")
    else:
        job["date_posted"] = None
    job["job_id"] = job.pop("id", None)
    fix_dict_str_or_none(job)


def _try_insert_job(job: dict) -> bool:
    """
    Inserts the job in the database if it doesn't exist, otherwise it just updates the existing job id.
    :param job: dictionary with job values.
    :return: True if successfully inserted or retrieved existing job id, False if failed.
    """
    existing_job = (
        supabase.table("job").select("id").eq("job_url", job["job_url"]).execute()
    )
    if existing_job.data and len(existing_job.data) > 0:
        job["id"] = existing_job.data[0]["id"]
        logger.info(f"Job with URL {job['job_url']} already exists. Skipping insert.")
        response = supabase.table("job").update("")
    else:
        response = supabase.table("job").insert(job, upsert=False).execute()
        if not response.data or len(response.data) <= 0:
            logger.error(f"Error storing job: {response.error.message}")
            return False
        else:
            job["id"] = response.data[0]["id"]
            logger.info(f"Stored job with ID: {response.data[0]['id']}")
    return True


def _try_insert_search_job(search_job: dict) -> bool:
    """
    Inserts the search job in the database if it doesn't exist.
    :param search_job: dictionary with job values.
    :return: True if successfully inserted or retrieved existing job id, False if failed.
    """
    existing_job = (
        supabase.table("search_job")
        .select("search_id", "job_id")
        .eq("search_id", search_job["search_id"])
        .eq("job_id", search_job["job_id"])
        .execute()
    )
    if existing_job.data and len(existing_job.data) > 0:
        logger.info(
            f"SearchJob with IDs {search_job['search_id']},{search_job['job_id']} already exists. Skipping insert."
        )
        return True
    response = supabase.table("search_job").insert(search_job, upsert=False).execute()
    if not response.data or len(response.data) <= 0:
        logger.error(f"Error storing job: {response.error.message}")
        return False
    else:
        logger.info(
            f"Stored job with ID: <{response.data[0]['search_id']},{response.data[0]['job_id']}>"
        )
    return True


def scrape_and_store_jobs(search: SearchEntry, is_new_search=False) -> None:
    # Job sources and search terms are stored as a comma separated list.
    job_sources = [item.strip() for item in search["job_source"].split(",")]
    search_terms = [item.strip() for item in search["search_term"].split(",")]
    for job_source in job_sources:
        for search_term in search_terms:
            try:
                jobs = scrape_jobs(
                    site_name=job_source,
                    search_term=search_term,
                    location=search["location"],
                    results_wanted=search["results_wanted"],
                    hours_old=HOURS_OLD_NEW if is_new_search else HOURS_OLD_UPDATE,
                    country_indeed=search["country"],  # Specific to Indeed
                    proxies=None,  # TODO Add proxies if needed
                    linkedin_fetch_description=job_source
                    == "linkedin",  # Specific to LinkedIn, unneeded for others.
                )

                for job in jobs.to_dict("records"):
                    try:
                        _format_job(job)
                        if not _try_insert_job(job):
                            continue

                        search_job = {"search_id": search["id"], "job_id": job["id"]}
                        _try_insert_search_job(search_job)
                    except Exception as e:
                        logger.error(f"Error during job storing: {str(e)}")

            except Exception as e:
                logger.error(f"Error during job scraping: {str(e)}")
