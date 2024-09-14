from typing import TypedDict, Optional
from datetime import datetime


class JobEntry(TypedDict):
    id: int
    site: Optional[str]
    job_url: Optional[str]
    job_url_direct: Optional[str]
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    job_type: Optional[str]
    date_posted: Optional[datetime]
    interval: Optional[str]
    min_amount: Optional[str]
    max_amount: Optional[str]
    currency: Optional[str]
    is_remote: Optional[bool]
    job_function: Optional[str]
    emails: Optional[str]
    description: Optional[str]
    company_url: Optional[str]
    logo_photo_url: Optional[str]
    created_at: Optional[datetime]
    site_id: Optional[str]
    matched_words: Optional[str]
    job_level: Optional[str]


JobEntryList = list[JobEntry]


class SearchEntry(TypedDict):
    id: int
    job_source: Optional[str]
    search_term: Optional[str]
    location: Optional[str]
    results_wanted: Optional[int]
    country: Optional[str]
    last_search: Optional[datetime]  # Using Optional for fields that can be None
    created_at: Optional[datetime]
    user_id: str
    last_processed: Optional[datetime]


# Define a type for the list of such dictionaries
SearchEntryList = list[SearchEntry]


class SearchJobEntry(TypedDict):
    search_id: int
    job_id: int
    created_at: datetime


SearchJobEntryList = list[SearchJobEntry]


class MissingRatingEntry(TypedDict):
    job_id: int
    resume_id: int


MissingRatingEntryList = list[MissingRatingEntry]
