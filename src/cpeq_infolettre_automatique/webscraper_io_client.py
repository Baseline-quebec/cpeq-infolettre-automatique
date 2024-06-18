"""Client module for WebScraper.io API interaction."""

import json
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        self.__api_token = api_token
        self.__base_url: str = "https://api.webscraper.io/api/v1"
        self.__headers: dict[str, str] = {"Content-Type": "application/json"}

    async def create_scraping_job(self, sitemap_id: str) -> str:
        """Creates a new scraping job for given sitemap id.

        Args:
            sitemap_id (str): ID of the Sitemap.

        Returns:
            str: ID of the created job.
        """
        url: str = f"{self.__base_url}/scraping-job"
        data: Any = {
            "sitemap_id": sitemap_id,
            "driver": "fulljs",
            "page_load_delay": 3000,
            "request_interval": 3000,
        }

        job_id: str
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers=self.__headers,
                params={"api_token": self.__api_token},
            )

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.exception(
                    "HTTP Code %s while creating scraping job on Sitemap ID %s.",
                    e.response.status_code,
                    sitemap_id,
                )
                raise
            except httpx.RequestError:
                logger.exception("Error issuing POST request at URL %s.", url)
                raise
            else:
                job_id = response.json().get("data", {}).get("id")

        return job_id

    async def get_scraping_jobs(self) -> list[str]:
        """Gets the list of scraping jobs from Webscraper.io.

        Returns:
            A list containing the IDs of all the scraping jobs.
        """
        url: str = f"{self.__base_url}/scraping-jobs"
        job_ids: list[str] = []

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"api_token": self.__api_token})

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.exception(
                    "HTTP code %s while getting all scraping jobs.",
                    e.response.status_code,
                )
                raise
            except httpx.RequestError:
                logger.exception("Error issuing GET request at URL %s.", url)
                raise
            else:
                job_ids = [job.id for job in response.json().get("data", [])]

        return job_ids

    async def download_scraping_job_data(self, job_id: str) -> list[dict[str, str]]:
        """Fetches raw JSON data for a scraping job and processes it into a structured format.

        Args:
            job_id (str): The job ID whose data is to be fetched.

        Returns:
            A list of JSON objects, represented as dictionaries.
            The Webscraper.io API returns JSON Lines
        """
        url: str = f"{self.__base_url}/scraping-job/{job_id}/json"
        job_data: list[dict[str, str]]

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params={"api_token", self.__api_token})
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.exception(
                    "HTTP Code %s while downloading scraping job data on Sitemap ID %s.",
                    e.response.status_code,
                    job_id,
                )
                raise
            except httpx.RequestError:
                logger.exception("Error issuing GET request at URL %s.", url)
                raise
            else:
                job_data = self.process_raw_response(response.text)

        return job_data

    @staticmethod
    def process_raw_response(raw_response: str) -> list[dict[str, str]]:
        """Converts raw JSON lines into a list of dictionaries (valid JSON array).

        Args:
        raw_response (str): The raw JSON lines to be processed.

        Returns:
            list[dict[str, str]]: A list of dictionaries or a list with an error message.
        """
        return [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]
