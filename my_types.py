from typing import TypedDict, Optional
from datetime import datetime


class JobSearchEntry(TypedDict):
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
JobSearchList = list[JobSearchEntry]
