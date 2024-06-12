"""Tests for the WebScraperIOClient and related functions."""

import logging
from unittest.mock import MagicMock

import pytest
from decouple import config
from httpx import HTTPStatusError, RequestError
from pytest_mock import MockerFixture

from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


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
new_scraping_job = 21417285  # unique scraping job test
all_scraping_jobs = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Scraping Download and process scraping job tests
scraping_job_id = 21395222  # unique scraping job test
multiple_job_ids = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Save to JSON tests
processed_scraping_job_id = 21398005  # unique scraping job test
processed_scraping_jobs_ids = ["21417285", "21416924", "21398005"]  # multiple scraping job test


@pytest.fixture()
def client() -> WebScraperIoClient:
    """Fixture to initialize WebScraperIoClient with API key from environment."""
    try:
        return WebScraperIoClient(api_token=config("WEBSCRAPER_IO_API_KEY"))
    except HTTPStatusError:
        return MagicMock(spec=WebScraperIoClient)


class TestWebscraperIoClient:
    """Test Webscraper.io client."""

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_create_scraping_jobs(client: WebScraperIoClient) -> None:
        """Test creating scraping jobs using WebScraperIOClient.

        Ensures that the create_scraping_jobs method returns a list of job IDs.
        """
        job_ids = client.create_scraping_jobs(sitemaps)
        if not isinstance(job_ids, list):
            error_message = "Expected job_ids to be a list"
            raise TypeError(error_message)
        if not all(isinstance(job_id, str) for job_id in job_ids):
            error_message = "ll job IDs should be strings"
            raise TypeError(error_message)
        logging.info("test_create_scraping_jobs passed")

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_get_scraping_job_details_sucess(client: WebScraperIoClient) -> None:
        """Test retrieving details of a scraping job."""
        if not sitemaps:
            pytest.skip(reason="No sitemaps available for testing.")
        details = client.get_scraping_job_details(all_scraping_jobs)
        if not isinstance(details, dict):
            error_message = "Job details should be a dictionary"
            raise TypeError(error_message)
        logging.info("Job details retrieved successfully: %s", details)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_create_scraping_jobs_failure(
        client: WebScraperIoClient, mocker: MockerFixture
    ) -> None:
        """Test failure in creating scraping jobs due to API errors."""
        mocker.patch(
            "httpx.post", side_effect=HTTPStatusError(message="Error", request=None, response=None)
        )
        with pytest.raises(HTTPStatusError):
            client.create_scraping_jobs(sitemaps)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_get_scraping_job_details_failure(client: WebScraperIoClient) -> None:
        """Test retrieval of details for a non-existent job to simulate failure."""
        job_id = "non_existent_job_id"
        result = client.get_scraping_job_details(job_id)
        if "error" not in result:
            error_message = "Expected an error for non-existent job"
            raise AssertionError(error_message)
        logging.info("test_get_scraping_job_details for non-existent job passed")

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_download_scraping_job_data_sucess(client: WebScraperIoClient) -> None:
        """Test downloading and processing data from a scraping job."""
        data = client.download_scraping_job_data(scraping_job_id)
        if not isinstance(data, list):
            error_message = "Expected the data to be a list"
            raise TypeError(error_message)
        logging.info("Data downloaded and processed successfully: %s", data)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_download_scraping_job_data_failure(client: WebScraperIoClient) -> None:
        """Testing with an invalid job ID."""
        result = client.download_scraping_job_data("invalid_job_id")
        if "error" not in result:
            error_message = "Expected an error message in the result when using an invalid job ID"
            raise AssertionError(error_message)
        logging.info("Handled invalid job ID correctly with error message: %s", result)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_download_and_process_multiple_jobs_success(client: WebScraperIoClient) -> None:
        """Test downloading and processing multiple scraping jobs successfully."""
        valid_job_ids = ["21417285", "21416924", "21398005"]
        combined_data = client.download_and_process_multiple_jobs(valid_job_ids)
        if not isinstance(combined_data, list):
            error_message = "Expected combined data to be a list"
            raise TypeError(error_message)
        if not all(isinstance(item, dict) for item in combined_data):
            error_message = "Each item in combined data should be a dictionary"
            raise AssertionError(error_message)
        logging.info(
            "Data from multiple jobs downloaded and processed successfully: %s", combined_data
        )

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    @pytest.mark.parametrize("invalid_id", ["invalid_id1", "invalid_id2", "invalid_id3"])
    def test_download_and_process_multiple_jobs_failure(
        client: WebScraperIoClient, invalid_id: str
    ) -> None:
        """Test handling failures when downloading and processing multiple scraping jobs with invalid IDs."""
        results = client.download_and_process_multiple_jobs([invalid_id])
        if not isinstance(results, list):
            error_message = "Expected a list even if it contains error details."
            raise TypeError(error_message)
        if not all("error" in result for result in results):
            error_message = "Each result should contain an 'error' key."
            raise ValueError(error_message)
        logging.info("Error processing detected correctly for %s: %s", invalid_id, results)

    # Tests créer par Chat GPT avec MonkeyPatch (Src: https://docs.pytest.org/en/latest/how-to/monkeypatch.html)
    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_create_scraping_jobs_failure_gpt(
        client: WebScraperIoClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test failure in creating scraping jobs due to API errors."""

        def mock_post() -> None:
            error_message = "Error"
            raise HTTPStatusError(error_message, request=None, response=None)

        monkeypatch.setattr("httpx.post", mock_post)

        with pytest.raises(HTTPStatusError):
            client.create_scraping_jobs(sitemaps)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_get_scraping_job_details_failure_gpt(
        client: WebScraperIoClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test failure in retrieving scraping job details due to network issues."""

        def mock_get() -> None:
            error_message = "Network error"
            raise RequestError(error_message, request=None)

        monkeypatch.setattr("httpx.get", mock_get)

        with pytest.raises(RequestError):
            client.get_scraping_job_details(new_scraping_job)

    @staticmethod
    @pytest.mark.skip(reason="Not mocked yet")
    def test_download_scraping_job_data_failure_gpt(
        client: WebScraperIoClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test failure in downloading scraping job data due to server issues."""

        def mock_get() -> None:
            error_message = "Server error"
            raise HTTPStatusError(error_message, request=None, response=None)

        monkeypatch.setattr("httpx.get", mock_get)

        with pytest.raises(HTTPStatusError):
            client.download_scraping_job_data(scraping_job_id)
