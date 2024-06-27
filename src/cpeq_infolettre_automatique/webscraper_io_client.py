"""Client module for WebScraper.io API interaction."""

import asyncio
import json
import logging
from datetime import date
from typing import ClassVar

import httpx

from cpeq_infolettre_automatique.schemas import News


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebscraperIoClient:
    """A client for interacting with the WebScraper.io API.

    This class provides methods to create scraping jobs,
    retrieve job details, and download job data.
    """

    _base_url: ClassVar[str] = "https://api.webscraper.io/api/v1"
    _headers: ClassVar[dict[str, str]] = {"Content-Type": "application/json"}

    def __init__(self, http_client: httpx.AsyncClient, api_token: str) -> None:
        """Initialize the WebScraperIoClient with the provided API token.

        Args:
            http_client (httpx.AsyncClient): The AsyncClient used for API calls.
            api_token (str): The API token used for authentication.
        """
        self._client = http_client
        self._api_token = api_token

    async def create_scraping_job(self, sitemap_id: str) -> str:
        """Creates a new scraping job for given sitemap id.

        Args:
            sitemap_id (str): ID of the Sitemap.

        Returns:
            str: ID of the created job on success, empty string otherwise.
        """
        url: str = f"{self._base_url}/scraping-job"
        data: dict[str, str | int] = {
            "sitemap_id": sitemap_id,
            "driver": "fulljs",
            "page_load_delay": 3000,
            "request_interval": 3000,
        }

        job_id: str = ""
        response = await self._client.post(
            url,
            json=data,
            headers=self._headers,
            params={"api_token": self._api_token},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(
                "HTTP Code %s while creating scraping job on Sitemap ID %s.",
                e.response.status_code,
                sitemap_id,
            )
        except httpx.RequestError:
            logger.exception("Error issuing POST request at URL %s.", url)
        else:
            job_id = str(response.json().get("data", {}).get("id"))

        return job_id

    async def delete_scraping_jobs(self) -> None:
        """Deletes all existing scraping jobs."""
        job_ids: list[str] = await self.get_scraping_jobs()
        coroutines = [self.delete_scraping_job(job_id) for job_id in job_ids]
        await asyncio.gather(*coroutines)

    async def delete_scraping_job(self, job_id: str) -> None:
        """Deletes an existing job with given id.

        Args:
            job_id (str): ID of the job to delete.
        """
        url: str = f"{self._base_url}/scraping-job/{job_id}"

        response: httpx.Response = await self._client.delete(
            url,
            params={"api_token": self._api_token},
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(
                "HTTP Code %s while deleting scraping job with ID %s.",
                e.response.status_code,
                job_id,
            )
        except httpx.RequestError:
            logger.exception("Error issuing DELETE request at URL %s.", url)

    async def get_scraping_jobs(self) -> list[str]:
        """Gets the list of scraping jobs from Webscraper.io.

        Returns:
            A list containing the IDs of all the scraping jobs.
        """
        url: str = f"{self._base_url}/scraping-jobs"
        job_ids: list[str] = []

        response: httpx.Response = await self._client.get(
            url, params={"api_token": self._api_token}
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.exception(
                "HTTP code %s while getting all scraping jobs.",
                e.response.status_code,
            )
        except httpx.RequestError:
            logger.exception("Error issuing GET request at URL %s.", url)
        else:
            job_ids = [str(job.id) for job in response.json().get("data", [])]

        return job_ids

    async def download_scraping_job_data(self, job_id: str) -> tuple[News, ...]:
        """Fetches raw JSON data for a scraping job and processes it into a structured format.

        Args:
            job_id (str): The job ID whose data is to be fetched.

        Returns:
            A list of JSON objects, represented as dictionaries.
            The Webscraper.io API returns JSON Lines
        """
        url: str = f"{self._base_url}/scraping-job/{job_id}/json"
        job_data: list[dict[str, str]] = []

        response = await self._client.get(url, params={"api_token": self._api_token})
        try:
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

        return tuple(
            News(
                title=data["title"],
                content=data["content"],
                date=date.fromisoformat(data["date"]),
                rubric="",
                summary="",
            )
            for data in job_data
        )

    @staticmethod
    def process_raw_response(raw_response: str) -> list[dict[str, str]]:
        """Converts raw JSON lines into a list of dictionaries (valid JSON array).

        Args:
        raw_response (str): The raw JSON lines to be processed.

        Returns:
            list[dict[str, str]]: A list of dictionaries or a list with an error message.
        """
        return [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]
