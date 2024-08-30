import common
from my_types import SearchJobEntry, SearchEntry
from helper import (
    fix_dict_str_or_none,
    parse_delimited_string,
    list_to_delimited_string,
)
from jobspy import scrape_jobs
import datetime
from supabase import Client

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
client = common.get_openai_client()

HOURS_OLD_NEW = 24
HOURS_OLD_UPDATE = 4


def _format_job(job) -> None:
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
    existing_job_response = (
        supabase.table("job").select("*").eq("job_url", job["job_url"]).execute()
    )
    if existing_job_response.data and len(existing_job_response.data) > 0:
        existing_job = existing_job_response.data[0]
        job["id"] = existing_job["id"]
        logger.info(f"Job with URL {job['job_url']} already exists. Skipping insert.")

        existing_matched_words = parse_delimited_string(existing_job["matched_words"])
        new_matched_words = parse_delimited_string(job["matched_words"])
        combined_matched_words = list(set(existing_matched_words + new_matched_words))
        if not len(combined_matched_words) == len(existing_matched_words):
            existing_job["matched_words"] = list_to_delimited_string(
                combined_matched_words
            )
            response = (
                supabase.table("job")
                .update(existing_job)
                .eq("id", existing_job["id"])
                .execute()
            )
            logger.info(
                f"Job with URL {job['job_url']} updated matched words {existing_matched_words} -> {combined_matched_words}."
            )
    else:
        response = supabase.table("job").insert(job, upsert=False).execute()
        if not response.data or len(response.data) <= 0:
            logger.error(f"Error storing job: {response.error.message}")
            return False
        else:
            job["id"] = response.data[0]["id"]
            logger.info(f"Stored job with ID: {response.data[0]['id']}")
    return True


def _try_insert_search_job(search_job: SearchJobEntry) -> bool:
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
    job_sources = parse_delimited_string(search["job_source"])
    search_terms = parse_delimited_string(search["search_term"])
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
                        job["matched_words"] = search["search_term"]
                        if not _try_insert_job(job):
                            continue

                        search_job = {"search_id": search["id"], "job_id": job["id"]}
                        _try_insert_search_job(search_job)
                    except Exception as e:
                        logger.error(f"Error during job storing: {str(e)}")

            except Exception as e:
                logger.error(f"Error during job scraping: {str(e)}")
