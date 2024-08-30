from typing import TypedDict, Optional
from datetime import datetime


class SearchEntry(TypedDict):
    id: int
    job_source: str
    search_term: str
    location: str
    results_wanted: int
    country: str
    last_search: Optional[datetime]  # Using Optional for fields that can be None
    created_at: datetime
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
