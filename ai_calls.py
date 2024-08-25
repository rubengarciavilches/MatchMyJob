import json
from typing import Dict, Any

import common
import helper

# Initialize Logger, Supabase and OpenAI
logger = common.get_logger()
openai = common.get_openai_client()


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
    model = "gpt-4o-mini"
    token_limit = 450
    system_prompt = [
        {"role": "system", "content": "You are an expert job matching assistant."},
        {
            "role": "system",
            "content": """Based on the following job description, rate how well this resume matches the job, 
            from 0 to 10, and explain why in up to 200 words. Required experience in 
            periods of time is of huge importance and will significantly reduce rating if not satisfied, 
            in which case it will be explicitly stated with the precise amount of time 
            and the difference with the candidate. Will differentiate between MUST have and NICE to have. 
            You may fill in the following values if they are available, DO NOT make them up.
            {"interval": "[yearly, monthly, hourly, etc.] period that applies to min/max_amount", "min_amount": 0, "max_amount": 0, "currency": "USD or other cur code", "is_remote": false}
            """
        },
        {
            "role": "system",
            "content": """You may want to fill in additional data to display to the candidate following this format:
            {"display_data": [{"label": "display text"}]}
            Examples are: observed experience requirements vs candidate experience, point by point or total, etc.
            """
        },
        {
            "role": "system",
            "content": """Your justification will be JSON formatted following this template: 
            {"rating": 0, "justification": "justification"}
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
