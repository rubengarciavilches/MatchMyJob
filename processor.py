import json
from supabase import Client

import common
import my_types
from ai_calls import generate_rating
from helper import pdf_to_text

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
openai = common.get_openai_client()


def process_missing_ratings(missing_ratings: my_types.MissingRatingEntryList):
    for missing_rating in missing_ratings:
        try:
            response = supabase.table('job').select('*').eq('id', missing_rating["job_id"]).execute()
            if not response.data or len(response.data) <= 0:
                logger.error(f"Error fetching unprocessed jobs or job is missing with ID {missing_rating['job_id']}.")
                continue
            job = response.data[0]

            response = supabase.table('resume').select('*').eq('id', missing_rating["resume_id"]).execute()
            if not response.data or len(response.data) <= 0:
                logger.error(
                    f"Error fetching unprocessed jobs or resume is missing with ID {missing_rating['resume_id']}.")
                continue
            resume = response.data[0]

            candidate_data = f"""
            \n\nJob Title: {job['title']}
            \n\nJob Description: {job['description']}
            \n\nResume: {resume['content']}
            """
            try:
                # Make the API call to GPT
                job_data, rating_data = generate_rating(candidate_data)
                if not job_data:
                    continue

                update_response = supabase.table('job').update(job_data).eq('id', missing_rating['job_id']).execute()
                if not update_response.data or len(response.data) < 0:
                    logger.error(f"Error updating job with ID: {missing_rating['job_id']}")
                else:
                    logger.info(f"Processed job with ID: {missing_rating['job_id']}")

                rating_data['job_id'] = missing_rating['job_id']
                rating_data['resume_id'] = missing_rating['resume_id']

                response = supabase.table('rating').insert(rating_data).execute()
                if not response.data or len(response.data) < 0:
                    logger.error(f"Error inserting rating with IDs: {missing_rating['job_id']}, {missing_rating['resume_id']}")
                else:
                    logger.info(f"Processed rating with ID: {response.data[0]['id']}")

            except Exception as e:
                logger.error(
                    f"Error processing missing_rating with ID {missing_rating['job_id']}, {missing_rating['resume_id']}: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching job with ID {missing_rating['job_id']}: {str(e)}")