"""Client module for WebScraper.io API interaction."""

import logging
from typing import Any

import httpx
from decouple import config

from cpeq_infolettre_automatique.utils import process_raw_response


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebscraperIoClientTest:
    """A test client example for interacting with the WebScraper.io API."""

    def get_endpoint(self, url: str) -> dict[str, str]:
        """Fetches a response from the specified URL.

        Args:
            url (str): The target URL to fetch data from.

        Returns:
            dict[str, str]: The response as a dictionary.
        """
        response = httpx.get(url)
        return self._handle_response(response)

    @staticmethod
    def _handle_response(response: httpx.Response) -> dict[str, Any]:
        """Process and parse the response from an HTTP request.

        Args:
            response (httpx.Response): The HTTP response to handle.

        Returns:
            dict[str, str]: The parsed response or None if an error occurs.
        """
        try:
            output: dict[str, Any] = response.json()
        except:
            logger.exception("Failed to parse JSON from the response")
            raise
        else:
            return output


class WebScraperIoClient:
    """A client for interacting with the WebScraper.io API.

    This class provides methods to create scraping jobs,
    retrieve job details, and download job data.
    """

    def __init__(self, api_token: str) -> None:
        """Initialize the WebScraperIoClient with the provided API token.

        Args:
            api_token (str): The API token used for authentication.
        """
        self.api_token = config("WEBSCRAPER_IO_API_KEY")
        self.base_url: str = "https://api.webscraper.io/api/v1"
        self.headers: dict[str, str] = {"Content-Type": "application/json"}

    def create_scraping_jobs(self, sitemaps: list[str]) -> list[str]:
        """Starts scraping jobs for multiple sitemap IDs and returns their job IDs.

        Args:
            sitemaps (list[dict[str, str]]): List of sitemaps to start jobs.

        Returns:
            list[str]: List of job IDs created.
        """
        job_ids = []
        for sitemap_id in sitemaps:
            url = f"{self.base_url}/scraping-job"
            data = {
                "sitemap_id": sitemap_id,
                "driver": "fulljs",
                "page_load_delay": 3000,
                "request_interval": 3000,
            }
            response = httpx.post(
                url,
                json=data,
                headers=self.headers,
                params={"api_token": self.api_token},
            )
            response.raise_for_status()
            job_id = response.json().get("data", {}).get("id")
            if job_id:
                job_ids.append(str(job_id))  # Convert job ID to string
                logger.info("Job %s started for sitemap %s", job_id, sitemap_id)
            else:
                logger.warning("No job ID received for sitemap %s", sitemap_id)
        return job_ids

    @staticmethod
    def get_scraping_jobs() -> None:
        """Unimplemented method to get scraping jobs."""
        raise NotImplementedError

    def get_scraping_job_details(self, scraping_job_id: str) -> dict[str, Any]:
        """Retrieves details of a specific scraping job.

        Args:
            scraping_job_id (str): The job ID to fetch details.

        Returns:
            dict[str, str] | dict[str, int] | None: The details of the scraping job, or an error response.
        """
        url = f"{self.base_url}/scraping-job/{scraping_job_id}?api_token={self.api_token}"
        try:
            response = httpx.get(
                url,
                headers=self.headers,
                params={"api_token": self.api_token},
            )
            response.raise_for_status()
            output: dict[str, Any] = response.json()
        except httpx.HTTPStatusError:
            logger.exception("HTTP error while fetching details for job %s", scraping_job_id)
            raise
        except httpx.RequestError:
            logger.exception("Request error while fetching details for job %s", scraping_job_id)
            raise
        else:
            return output

    def download_scraping_job_data(self, scraping_job_id: str) -> str:
        """Fetches raw JSON data for a scraping job and processes it into a structured format.

        Args:
            scraping_job_id (str): The job ID whose data is to be fetched.

        Returns:
            str: The processed job data or an error message.
        """
        url = f"{self.base_url}/scraping-job/{scraping_job_id}/json?api_token={self.api_token}"
        try:
            response = httpx.get(url)
            response.raise_for_status()
        except:
            logger.exception("Failed to process data for job %s", scraping_job_id)
            raise
        else:
            return response.text

    def download_and_process_multiple_jobs(self, job_ids: list[str]) -> list[dict[str, str]]:
        """Converts raw JSON lines into a list of dictionaries (valid JSON array) and saves it into a dictionary.

        Args:
            job_ids (list[str]): List of job IDs to process.

        Returns:
            list[dict[str, str]]: Processed job data from all job IDs combined.
        """
        combined_data = []  # This will store all processed data

        for job_id in job_ids:
            logger.info("Starting download for Job ID: %s", job_id)
            raw_data = self.download_scraping_job_data(job_id)
            data = process_raw_response(raw_data)
            combined_data.extend(data)  # Add processed data to the combined list
            preview_limit = 2
            logger.info(
                "Processed data for job %s: %s",
                job_id,
                data[:2] if len(data) > preview_limit else data,
            )

        return combined_data
