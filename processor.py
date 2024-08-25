import json
from supabase import Client

import common
from ai_calls import generate_rating
from helper import pdf_to_text

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
supabase: Client = common.get_supabase_client()
openai = common.get_openai_client()


def process_jobs():
    try:
        # Retrieve unprocessed jobs from Supabase
        response = supabase.table('job').select('*').eq('status', 'unprocessed').execute()
        if not response.data:
            logger.error(f"Error fetching unprocessed jobs: {response.error.message}")
            return

        jobs = response.data

        for job in jobs:
            # Example: Processing the job using GPT-4
            job_title = job.get('title', '')
            job_description = job.get('description', '')
            resume = pdf_to_text("resume.pdf")  # Retrieve the candidate's resume

            candidate_data = f"""
            \n\nJob Title: {job_title}
            \n\nJob Description: {job_description}
            \n\nResume: {resume}
            """

            try:
                # Make the API call to GPT
                update_data = generate_rating(candidate_data)
                if not response:
                    continue

                # Update the job with GPT evaluation
                update_data = {
                    'rating': response['rating'],
                    'justification': response['justification'],
                    'status': 'processed'
                }

                update_response = supabase.table('job').update(update_data).eq('job_url', job['job_url']).execute()
                if not update_response.data:
                    logger.error(f"Error updating job with ID: {job['id']}")
                else:
                    logger.info(f"Processed job with ID: {job['id']}")

            except Exception as e:
                logger.error(f"Error processing job with ID {job['id']}: {str(e)}")

    except Exception as e:
        logger.error(f"Error during job processing: {str(e)}")

