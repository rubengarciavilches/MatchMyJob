import datetime
import json
import time
from typing import Dict, Any

import common
import helper

TIME_BETWEEN_CALLS = 21

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
openai = common.get_openai_client()
time_last_call = datetime.datetime.now()


def _generate_response(response_object: dict, model: str, token_limit: int, system_prompt: list, user_prompt: list,
                       temperature: float):
    # Extract mandatory fields
    rating = response_object.get('rating')
    justification = response_object.get('justification')

    # Extract optional fields
    interval = response_object.get('interval')
    min_amount = response_object.get('min_amount')
    max_amount = response_object.get('max_amount')
    currency = response_object.get('currency')
    is_remote = response_object.get('is_remote')
    display_data = response_object.get('display_data')

    job_data = {
        'interval': interval,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'currency': currency,
        'is_remote': is_remote,
    }

    rating_data = {
        'rating': rating,
        'justification': justification,
        'display_data': display_data,
        'model': model,
        'token_limit': token_limit,
        'system_prompt': json.dumps(system_prompt),
        'user_prompt': json.dumps(user_prompt),
        'temperature': temperature,
    }

    # Return all relevant data
    return job_data, rating_data


def generate_rating(candidate_data: str) -> tuple[dict, dict] | None:
    global time_last_call
    time_now = datetime.datetime.now()
    time_diff = (time_now - time_last_call).total_seconds()
    if time_diff < TIME_BETWEEN_CALLS:
        logger.info(f"Waiting for next request: {TIME_BETWEEN_CALLS - time_diff}")
        time.sleep(TIME_BETWEEN_CALLS - time_diff)
    time_last_call = datetime.datetime.now()

    model = "gpt-3.5-turbo"
    token_limit = 550
    system_prompt = [
        {
            "role": "system",
            "content": """
        You are an expert job matching assistant specialized in evaluating candidates with minimal professional experience.
        
        Task: Rate how well the resume matches the job description, from 0 to 10. Explain the rating in up to 200 words.

        Instructions:
        1. DO NOT imagine, invent, or fabricate any information.
        2. Consider alternative qualifications (e.g., academic achievements, internships, projects, transferable skills, overall potential) for candidates with limited experience.
        3. Prioritize "MUST have" requirements. Be flexible with "NICE to have" requirements.
        4. Provide constructive feedback where experience is lacking, and highlight compensating strengths.
        5. Fill in the following values if available (DO NOT make them up):
           - Interval: {"interval": "[yearly, monthly, hourly, etc.] period that applies to min/max_amount"}
           - Compensation: {"min_amount": 0, "max_amount": 0, "currency": "USD or other cur code"}
           - Work Type: {"is_remote": false/true}
        6. Include relevant additional data for the candidate using the following format:
           - {"display_data": [{"label": "display text"}]}
           - Examples: relevant coursework, skill matches, project experience.

        JSON Output Template:
        {
            "rating": 0,
            "justification": "justification",
            "display_data": [{"label": "", "content": ""}],
            "interval": "[yearly, monthly, hourly, etc.] period that applies to min/max_amount",
            "min_amount": 0,
            "max_amount": 0,
            "currency": "USD or other cur code",
            "is_remote": false/true
        }
        """
        }
    ]

    user_prompt = [{"role": "user", "content": candidate_data}]
    temperature = 0.5

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=system_prompt + user_prompt,
            max_tokens=token_limit,
            n=1,
            stop=None,
            temperature=temperature,
        )

        response_object = json.loads(response.choices[0].message.content)

        return _generate_response(
            response_object=response_object,
            model=model,
            token_limit=token_limit,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature
        )

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None


def clean_resume(content: str) -> dict[str] | None:
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume summary generator and confidential expert."},
                {
                    "role": "system",
                    "content": """You will receive a resume, summarize the content by removing 
                    unnecessary characters like * or [, or unneeded whitespace keep other characters untouched."""
                },
                {
                    "role": "system",
                    "content": """You will receive a resume, erase all personal data and details, retain every other 
                    data, reply in JSON following this template: {\"formatted_content\": \"\"}"""
                },
                {"role": "user", "content": content}
            ],
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        response_object = json.loads(response.choices[0].message.content)
        return {'formatted_content': response_object['formatted_content']}

    # except openai.error.RateLimitError:
    #     logger.warning("Rate limit exceeded. Retrying in 10 seconds...")
    #     time.sleep(10)
    #     return await call_gpt_api(prompt)

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None
