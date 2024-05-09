"""Tests for the WebScraperIOClient and related functions."""


import pytest
from decouple import config
from httpx import HTTPStatusError, RequestError

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

# Sitemaps tests
# sitemap_ids = [
#     "1127309",
#     "1120854",
#     "1125386",
# ]
# List of sitemap IDs, FAQDD ne se trouvait rien et bloquait!
# sitemap_ids = ["1125386"]

# Start Scraping job tests
new_scraping_job = 21417285  # unique scraping job test
all_scraping_jobs = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Scraping Download and process scraping job tests
scraping_job_id = 21395222  # unique scraping job test
multiple_job_ids = ["21417285", "21416924", "21398005"]  # multiple scraping job test

# Save to JSON tests
processed_scraping_job_id = 21398005  # unique scraping job test
processed_scraping_jobs_ids = ["21417285", "21416924", "21398005"]  # multiple scraping job test


class TestWebscraperIoClient:
    """Test Webscraper.io client."""

    @pytest.fixture()
    @staticmethod
    def client():
        """Fixture to initialize WebScraperIoClient with API key from environment."""
        return WebScraperIoClient(api_token=config("WEBSCRAPER_IO_API_KEY"))

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_create_scraping_jobs(client) -> None:
        """Test creating scraping jobs using WebScraperIOClient.

        Ensures that the create_scraping_jobs method returns a list of job IDs.
        """
        job_ids = client.create_scraping_jobs(sitemaps)
        assert isinstance(job_ids, list), "Expected job_ids to be a list"
        assert all(isinstance(job_id, str) for job_id in job_ids), "All job IDs should be strings"
        print("test_create_scraping_jobs passed")

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_get_scraping_job_details_sucess(client):
        """Test retrieving details of a scraping job."""
        if not sitemaps:
            pytest.skip("No sitemaps available for testing.")
        details = client.get_scraping_job_details(all_scraping_jobs)
        assert isinstance(details, dict), "Job details should be a dictionary."
        print("Job details retrieved successfully:", details)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_create_scraping_jobs_failure(client, mocker):
        """Test failure in creating scraping jobs due to API errors."""
        mocker.patch(
            "httpx.post", side_effect=HTTPStatusError(message="Error", request=None, response=None)
        )
        with pytest.raises(HTTPStatusError):
            client.create_scraping_jobs(sitemaps)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_get_scraping_job_details_failure(client):
        """Test retrieval of details for a non-existent job to simulate failure."""
        job_id = "non_existent_job_id"
        result = client.get_scraping_job_details(job_id)
        assert "error" in result, "Expected an error for non-existent job"
        print("test_get_scraping_job_details for non-existent job passed")

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_download_scraping_job_data_sucess(client):
        """Test downloading and processing data from a scraping job."""
        data = client.download_scraping_job_data(scraping_job_id)
        assert isinstance(data, list), "Expected the data to be a list."
        print("Data downloaded and processed successfully:", data)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_download_scraping_job_data_failure(client):
        """Testing with an invalid job ID."""
        result = client.download_scraping_job_data("invalid_job_id")
        assert (
            "error" in result
        ), "Expected an error message in the result when using an invalid job ID."
        print("Handled invalid job ID correctly with error message:", result)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_download_and_process_multiple_jobs_success(client):
        """Test downloading and processing multiple scraping jobs successfully."""
        valid_job_ids = ["21417285", "21416924", "21398005"]
        combined_data = client.download_and_process_multiple_jobs(valid_job_ids)
        assert isinstance(combined_data, list), "Expected combined data to be a list."
        assert all(
            isinstance(item, dict) for item in combined_data
        ), "Each item in combined data should be a dictionary."
        print("Data from multiple jobs downloaded and processed successfully:", combined_data)

    @pytest.skip("Not mocked yet")
    @staticmethod
    @pytest.mark.parametrize("invalid_id", ["invalid_id1", "invalid_id2", "invalid_id3"])
    def test_download_and_process_multiple_jobs_failure(client, invalid_id):
        """Test handling failures when downloading and processing multiple scraping jobs with invalid IDs."""
        results = client.download_and_process_multiple_jobs([invalid_id])
        assert isinstance(results, list), "Expected a list even if it contains error details."
        assert all(
            "error" in result for result in results
        ), "Each result should contain an 'error' key."
        print(f"Error processing detected correctly for {invalid_id}: ", results)


# Tests créer par Chat GPT avec MonkeyPatch (Src: https://docs.pytest.org/en/latest/how-to/monkeypatch.html)
    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_create_scraping_jobs_failure_gpt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test failure in creating scraping jobs due to API errors."""

        def mock_post(*args, **kwargs) -> None:
            error_message = "Error"
            raise HTTPStatusError(error_message, request=None, response=None)

        monkeypatch.setattr("httpx.post", mock_post)

        with pytest.raises(HTTPStatusError):
            self.create_scraping_jobs(sitemaps)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_get_scraping_job_details_failure_gpt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test failure in retrieving scraping job details due to network issues."""

        def mock_get(*args, **kwargs) -> None:
            error_message = "Network error"
            raise RequestError(error_message, request=None)

        monkeypatch.setattr("httpx.get", mock_get)

        with pytest.raises(RequestError):
            self.get_scraping_job_details(new_scraping_job)

    @pytest.skip("Not mocked yet")
    @staticmethod
    def test_download_scraping_job_data_failure_gpt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test failure in downloading scraping job data due to server issues."""

        def mock_get(*args, **kwargs) -> None:
            error_message = "Server error"
            raise HTTPStatusError(error_message, request=None, response=None)

        monkeypatch.setattr("httpx.get", mock_get)

        with pytest.raises(HTTPStatusError):
            self.download_scraping_job_data(scraping_job_id)
