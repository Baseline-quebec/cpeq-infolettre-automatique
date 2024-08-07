"""Client module for WebScraper.io API interaction."""

import asyncio
import datetime as dt
import json
import logging
from collections.abc import Iterable
from types import MappingProxyType

import httpx
from httpx import HTTPStatusError, Response
from pydantic import ValidationError

from cpeq_infolettre_automatique.schemas import News, ScrapingProblem


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
RATELIMIT_RESET_HEADER = "x-ratelimit-reset"
RATELIMIT_ERROR_CODE = 429
SECONDS_IN_MINUTE = 60
LIMIT_MAX_SECONDS = 15 * SECONDS_IN_MINUTE


class WebscraperIoClient:
    """A client for interacting with the WebScraper.io API.

    This class provides methods to create scraping jobs,
    retrieve job details, and download job data.
    """

    _base_url = "https://api.webscraper.io/api/v1"
    _headers = MappingProxyType({"Content-Type": "application/json"})

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

    async def create_scraping_jobs(self) -> list[str]:
        """Creates scraping jobs for all sitemaps.

        Returns:
            A list containing the IDs of all the created scraping jobs.
        """
        sitemaps: list[dict[str, str]] = await self.get_sitemaps()
        job_ids: list[str] = []
        coroutines = [self.create_scraping_job(sitemap["id"]) for sitemap in sitemaps]
        job_ids = await asyncio.gather(*coroutines)
        return job_ids

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
            if e.response.status_code == RATELIMIT_ERROR_CODE:
                await self._handle_throttling(response)
                return await self.delete_scraping_job(job_id=job_id)
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
            if e.response.status_code == RATELIMIT_ERROR_CODE:
                await self._handle_throttling(response)
                return await self.get_scraping_jobs()
        except httpx.RequestError:
            logger.exception("Error issuing GET request at URL %s.", url)
        else:
            job_ids = [str(job["id"]) for job in response.json().get("data", [])]
        return job_ids

    async def get_all_scraping_problems(
        self, job_ids: list[str] | None = None
    ) -> list[ScrapingProblem]:
        """Returns a dictionary of all the problems who arose for each scraping job."""
        if job_ids is None:
            job_ids = await self.get_scraping_jobs()
        coroutines = [self.get_scraping_job_problems(job_id) for job_id in job_ids]
        site_problems: list[ScrapingProblem] = [
            problem
            for job_problems in await asyncio.gather(*coroutines)
            for problem in job_problems
        ]
        return site_problems

    async def get_scraping_job_problems(self, job_id: str) -> Iterable[ScrapingProblem]:
        """Returns a dictionary of scraping problems who arose for a given scraping job."""
        url = f"{self._base_url}/scraping-job/{job_id}/problematic-urls"
        data: list[ScrapingProblem] = []
        response = await self._client.get(url, params={"api_token": self._api_token})

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == RATELIMIT_ERROR_CODE:
                await self._handle_throttling(response)
                return await self.get_scraping_job_problems(job_id)
            logger.exception(
                "HTTP code %s while getting scraping job problems with job ID %s.",
                e.response.status_code,
                job_id,
            )
        except httpx.RequestError:
            logger.exception("Error issuing GET request at URL %s.", url)
        else:
            data = [
                ScrapingProblem(url=site_problem.url, type=site_problem.type)
                for site_problem in response.json().get("data", [])
            ]
        return data

    async def download_scraping_job_data(self, job_id: str) -> Iterable[News]:
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
        except HTTPStatusError as e:
            if e.response.status_code == RATELIMIT_ERROR_CODE:
                await self._handle_throttling(response)
                return await self.download_scraping_job_data(job_id)
            logger.exception(
                "HTTP Code %s while downloading scraping job data on Sitemap ID %s.",
                e.response.status_code,
                job_id,
            )
        except httpx.RequestError:
            logger.exception("Error issuing GET request at URL %s.", url)
        else:
            job_data = self.process_raw_response(response.text)

        news = []
        for data in job_data:
            try:
                news.append(News.model_validate(data))
            except ValidationError:
                logger.exception("Error while processing news data")
        return tuple(news)

    async def get_sitemaps(self) -> list[dict[str, str]]:
        """Gets the list of sitemaps from Webscraper.io.

        Returns:
            A list containing the IDs and names of all the sitemaps.
        """
        url: str = f"{self._base_url}/sitemaps"
        sitemaps: list[dict[str, str]] = []
        response: httpx.Response = await self._client.get(
            url, params={"api_token": self._api_token}
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == RATELIMIT_ERROR_CODE:
                await self._handle_throttling(response)
                return await self.get_sitemaps()
            logger.exception(
                "HTTP code %s while getting all sitemaps.",
                e.response.status_code,
            )
        except httpx.RequestError:
            logger.exception("Error issuing GET request at URL %s.", url)
        else:
            sitemaps = response.json().get("data", [])
        return sitemaps

    @staticmethod
    def process_raw_response(raw_response: str) -> list[dict[str, str]]:
        """Converts raw JSON lines into a list of dictionaries (valid JSON array).

        Args:
        raw_response (str): The raw JSON lines to be processed.

        Returns:
            list[dict[str, str]]: A list of dictionaries or a list with an error message.
        """
        if not raw_response:
            return []
        return [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]

    @staticmethod
    async def _handle_throttling(response: Response) -> None:
        """Handles HTTP 429 Too Many Requests."""
        timestamp = response.headers.get(RATELIMIT_RESET_HEADER)
        if timestamp is not None:
            datetime_reset = dt.datetime.fromtimestamp(int(timestamp), tz=dt.UTC)
            seconds_to_reset = (datetime_reset - dt.datetime.now(tz=dt.UTC)).total_seconds() + 1
        else:
            seconds_to_reset = LIMIT_MAX_SECONDS
            warning_msg = "Webscraper.io rate limit reached, retrying in %s seconds."
            logging.warning(warning_msg, seconds_to_reset)
            await asyncio.sleep(seconds_to_reset)
