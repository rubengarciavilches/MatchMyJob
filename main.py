import datetime
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from supabase import Client

import common
import db_queries
import helper
import my_db
import my_types
import scraper

# https://github.com/Bunsly/JobSpy
# https://github.com/openai/openai-python
# https://supabase.com/docs/reference/python

# Constants
# JOB_SOURCES = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
# SEARCH_TERMS = ["java", "intern developer", "early career software", "new grad software", "python", "typescript"]
# LOCATION = "Minneapolis"
# RESULTS_WANTED = 100
# HOURS_OLD = 24

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
client = common.get_openai_client()


def get_outdated_searches() -> my_types.JobSearchList | None:
    try:
        # Get the current time in UTC
        now = datetime.datetime.utcnow()

        # Define the time threshold (3 hours ago)
        three_hours_ago = now - datetime.timedelta(hours=3)

        # Query Supabase for rows where "last_search" is NULL or "last_search" + 3 hours is less than now
        no_searches = supabase.table('search').select('*').filter(
            'last_search', 'is', 'null'
        ).execute()
        outdated_searches = supabase.table('search').select('*').filter(
            'last_search', 'lte', three_hours_ago.isoformat()
        ).execute()

        response = no_searches.data + outdated_searches.data

        return response

    except Exception as e:
        logger.error(f"An error occurred while retrieving outdated searches: {e}")
        return None


def set_search_last_updated(search: my_types.JobSearchEntry):
    try:
        # Get the current time in UTC
        now = helper.now_formatted_datetime()

        update_data = {
            'last_search': now
        }

        response = supabase.table('search').update(update_data).eq('id', search['id']).execute()
        if not response.data or len(response.data) <= 0:
            logger.error(f"Error storing search: {response.error.message}")
        else:
            logger.info(f"Stored search with ID: {response.data[0]['id']}")

    except Exception as e:
        logger.error(f"Error during search scraping or storing: {str(e)}")


def get_missing_ratings():
    """
    The missing ratings will be the ones that: There is a search_job, but the user that triggered it has no resume
    together with it on ratings table.
    :return:
    """
    try:
        rows = my_db.run_query(db_queries.missing_ratings)

        if not rows:
            logger.error(f"Error retrieving missing ratings.")
            return None

        rows = [{'job_id': row[0], 'resume_id': row[1]} for row in rows]
        logger.info(f"Retrieved {len(rows)} missing ratings.")
        return rows

    except Exception as e:
        logger.error(f"An error occurred while retrieving missing ratings: {e}")
        return None


def scrape_it():
    for search in get_outdated_searches():
        scraper.scrape_and_store_jobs(search)
        set_search_last_updated(search)


def process_it():
    get_missing_ratings()


def main():
    scrape_it()
    process_it()


if __name__ == "__main__":
    main()
