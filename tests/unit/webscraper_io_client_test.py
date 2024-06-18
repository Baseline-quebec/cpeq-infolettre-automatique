"""Unit Tests for the Webscraper.io client class."""

from unittest.mock import MagicMock

import httpx
import pytest


@pytest.fixture()
def http_client_fixture() -> httpx.AsyncClient:
    """httpx.AsyncClient fixture."""
    return MagicMock(httpx.AsyncClient)


sitemaps: list[dict[str, str]] = [
    {
        "name": "Ciraig",
        "url": "https://ciraig.org/index.php/fr/category/actualites/",
        "sitemap_id": "1127309",
    },
    {
        "name": "CIRODD",
        "url": "https://cirodd.org/actualites/",
        "sitemap_id": "1120854",
    },
    {
        "name": "FAQDD",
        "url": "https://faqdd.qc.ca/publications/",
        "sitemap_id": "1120853",
    },
    {
        "name": "ECPAR",
        "url": "http://www.ecpar.org/fr/nouvelles/",
        "sitemap_id": "1125386",
    },
]

# Sitemaps tests # sitemap_ids = [
#     "1127309",
#     "1120854",
#     "1125386", ]
# List of sitemap IDs, FAQDD ne se trouvait rien et bloquait!
# sitemap_ids = ["1125386"]  # noqa: ERA001

# Start Scraping job tests
new_scraping_job = "21417285"  # unique scraping job test
all_scraping_jobs = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Scraping Download and process scraping job tests
scraping_job_id = "21395222"  # unique scraping job test
multiple_job_ids = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Save to JSON tests
processed_scraping_job_id = "21398005"  # unique scraping job test
processed_scraping_jobs_ids = [
    "21417285",
    "21416924",
    "21398005",
]  # multiple scraping job test


class WebscraperIoClientTests:
    """Test Webscraper.io client."""

    @staticmethod
    def given_happy_path__when_create_scraping_job__then_return_job_id__test() -> None:
        """create_scraping_job should return the newly created Job ID on a happy path."""
        raise NotImplementedError

    @staticmethod
    def given_http_status_error__when_create_scraping_job__then_log_and_raise__test() -> None:
        """create_scraping_job should log and raise when an HTTPStatusError is raised."""
        raise NotImplementedError

    @staticmethod
    def given_request_error__when_create_scraping_job__then_log_and_raise__test() -> None:
        """create_scraping_job should log and raise when a RequestError is raised."""
        raise NotImplementedError

    @staticmethod
    def given_happy_path__when_get_scraping_jobs__then_return_job_ids__test() -> None:
        """get_scraping_jobs should return all the job ids on a happy path."""
        raise NotImplementedError

    @staticmethod
    def given_http_status_error__when_get_scraping_jobs__then_log_and_raise__test() -> None:
        """get_scraping_jobs should log and raise when an HTTPStatusError is raised."""
        raise NotImplementedError

    @staticmethod
    def given_request_error__when_get_scraping_jobs__then_log_and_raise__test() -> None:
        """get_scraping_jobs should log and raise when a RequestError is raised."""
        raise NotImplementedError

    @staticmethod
    def given_happy_path__when_download_scraping_job_data__then_return_data__test() -> None:
        """download_scraping_job_data should return job data on a happy path."""
        raise NotImplementedError

    @staticmethod
    def given_http_status_error__when_download_scraping_job_data__then_log_and_raise__test() -> (
        None
    ):
        """download_scraping_job_data should log and raise when an HTTPStatusError is raised."""
        raise NotImplementedError

    @staticmethod
    def given_request_error__when_download_scraping_job_data__then_log_and_raise__test() -> None:
        """download_scraping_job_data should log and raise when a RequestError is raised."""
        raise NotImplementedError
