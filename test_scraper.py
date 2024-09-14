import unittest
from scraper import _format_jobs
import pandas as pd
import numpy as np


class TestFormatJobs(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "site": "linkedin",
            "job_url": "https://www.linkedin.com/jobs/view/4015437876",
            "job_url_direct": "https://www.adzuna.com/details/4713544957",
            "title": "Team Leader, Distribution",
            "company": "Path Engineering",
            "location": "Plymouth, MN",
            "job_type": "fulltime",
            "date_posted": None,
            "interval": None,
            "min_amount": None,
            "max_amount": None,
            "currency": None,
            "is_remote": None,
            "job_function": "Information Technology",
            "emails": None,
            "description": "Description example",
            "company_url": "https://www.linkedin.com/company/pathengineering",
            "logo_photo_url": "https://media.licdn.com/dms/image/v2/C560BAQHr0_yvFJGXMg.jpg",
            "site_id": "4015437876",
            "matched_words": None,
            "job_level": "mid-senior level",
        }
        # Define the dictionary
        data = {
            "id": "4015437876",
            "site": "linkedin",
            "job_url": "https://www.linkedin.com/jobs/view/4015437876",
            "job_url_direct": "https://www.adzuna.com/details/4713544957",
            "title": "Team Leader, Distribution",
            "company": "Path Engineering",
            "location": "Plymouth, MN",
            "job_type": "fulltime",
            "date_posted": None,
            "salary_source": np.nan,
            "interval": np.nan,
            "min_amount": np.nan,
            "max_amount": np.nan,
            "currency": np.nan,
            "is_remote": None,
            "job_level": "mid-senior level",
            "job_function": "Information Technology",
            "company_industry": "Engines and Power Transmission Equipment Manufacturing",
            "listing_type": None,
            "emails": None,
            "description": "Description example",
            "company_url": "https://www.linkedin.com/company/pathengineering",
            "company_url_direct": None,
            "company_addresses": None,
            "company_num_employees": None,
            "company_revenue": None,
            "company_description": None,
            "logo_photo_url": "https://media.licdn.com/dms/image/v2/C560BAQHr0_yvFJGXMg.jpg",
            "banner_photo_url": None,
            "ceo_name": None,
            "ceo_photo_url": None,
        }

        # Convert the dictionary into a pandas DataFrame
        self.jobs_df = pd.DataFrame([data])

    def test_format_jobs(self):
        result = _format_jobs(self.jobs_df)
        self.assertEqual(result[0], self.expected)


if __name__ == "__main__":
    unittest.main()
