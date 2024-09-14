from typing import Optional

from pandas import DataFrame

import common
from my_types import SearchJobEntry, SearchEntry, JobEntry, JobEntryList
from helper import (
    parse_delimited_string,
    list_to_delimited_string,
)
from jobspy import scrape_jobs
from datetime import datetime
from supabase import Client

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
client = common.get_openai_client()

HOURS_OLD_NEW = 24
HOURS_OLD_UPDATE = 4


def _format_jobs(jobs_df: DataFrame) -> JobEntryList:
    """
    Formats the jobs received from JobSpy to remove unnecessary fields and change the format of others to be ready to
    upload it.
    :param jobs_df: dataframe of jobs received from JobSpy
    :return: List of formatted job entries
    """
    # Will go through all of this keys and ignore the additional ones in the job received.
    expected_keys = {
        # "id": int, We will get the id from the database insert response.
        "site": Optional[str],
        "job_url": Optional[str],
        "job_url_direct": Optional[str],
        "title": Optional[str],
        "company": Optional[str],
        "location": Optional[str],
        "job_type": Optional[str],
        "date_posted": Optional[datetime],
        "interval": Optional[str],
        "min_amount": Optional[str],
        "max_amount": Optional[str],
        "currency": Optional[str],
        "is_remote": Optional[bool],
        "job_function": Optional[str],
        "emails": Optional[str],
        "description": Optional[str],
        "company_url": Optional[str],
        "logo_photo_url": Optional[str],
        "site_id": Optional[str],
        "matched_words": Optional[str],
        "job_level": Optional[str],
    }

    filtered_jobs: JobEntryList = []
    jobs_raw = jobs_df.to_dict("records")
    for job_raw in jobs_raw:
        job_raw["site_id"] = job_raw["id"]
        filtered_job: JobEntry = {}
        for key, expected_type in expected_keys.items():
            value = job_raw.pop(key, None)
            if value is None or isinstance(value, expected_type):
                filtered_job[key] = value
            elif expected_type == Optional[datetime] and isinstance(value, datetime):
                try:
                    filtered_job[key] = value.strftime("%Y-%m-%d")
                except ValueError:
                    filtered_job[key] = None
            else:
                filtered_job[key] = None
        filtered_jobs.append(filtered_job)
    return filtered_jobs


def _try_insert_job(job: JobEntry) -> JobEntry | None:
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
            return None
        else:
            job["id"] = response.data[0]["id"]
            logger.info(f"Stored job with ID: {response.data[0]['id']}")
    return job


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
            f"Stored search job with ID: <{response.data[0]['search_id']},{response.data[0]['job_id']}>"
        )
    return True


def scrape_and_store_jobs(search: SearchEntry, is_new_search=False) -> None:
    # Job sources and search terms are stored as a comma separated list.
    job_sources = parse_delimited_string(search["job_source"])
    search_terms = parse_delimited_string(search["search_term"])
    for job_source in job_sources:
        for search_term in search_terms:
            try:
                jobs_df = scrape_jobs(
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

                for job in _format_jobs(jobs_df):
                    try:
                        job["matched_words"] = search["search_term"]
                        inserted_job = _try_insert_job(job)
                        if inserted_job is None:
                            logger.error(f"Error during job storing: {str(e)}")
                            continue

                        search_job = {
                            "search_id": search["id"],
                            "job_id": inserted_job["id"],
                        }
                        _try_insert_search_job(search_job)
                    except Exception as e:
                        logger.error(f"Error during job storing: {str(e)}")

            except Exception as e:
                logger.error(f"Error during job scraping: {str(e)}")
