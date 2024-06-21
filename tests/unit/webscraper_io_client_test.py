"""Unit Tests for the Webscraper.io client class."""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, HTTPStatusError, RequestError, Response

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


@pytest.fixture()
def scraping_job_data_fixture() -> str:
    """Scraping job data fixture."""
    with Path("tests", "unit", "test_data", "scraped_data.txt").open() as file:
        return file.read()


@pytest.fixture()
def async_client_fixture() -> AsyncClient:
    """AsyncClient fixture."""
    return AsyncClient()


@pytest.mark.asyncio(scope="class")
class WebscraperIoClientTest:
    """Webscraper.io Client tests."""

    @staticmethod
    async def given_happy_path__when_create_scraping_job__then_return_job_id__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return the newly created Job ID on a happy path."""
        # Given
        job_id: str = "job_id"
        response: Response = Response()
        json: Any = {"data": {"id": job_id}}
        response.json = MagicMock(return_value=json)
        async_client_fixture.post = MagicMock(return_value=response)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert return_value == job_id

    @staticmethod
    async def given_http_status_error__when_create_scraping_job__then_return_empty_string__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return empty string when an HTTPStatusError is raised."""
        # Given
        async_client_fixture.post = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert return_value == ""

    @staticmethod
    async def given_request_error__when_create_scraping_job__then_return_empty_string__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return empty string when a RequestError is raised."""
        # Given
        async_client_fixture.post = AsyncMock(side_effet=RequestError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert return_value == ""

    @staticmethod
    async def given_happy_path__when_get_scraping_jobs__then_return_job_ids__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return all the job ids on a happy path."""
        # Given
        job_ids: list[str] = ["1", "2", "3"]
        response: Response = Response(status_code=200)
        json: Any = {"data": [{"id": job_id} for job_id in job_ids]}
        response.json = MagicMock(return_value=json)
        async_client_fixture.get = AsyncMock(return_value=response)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert return_value == job_ids

    @staticmethod
    async def given_http_status_error__when_get_scraping_jobs__then_return_empty_array__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return empty array when an HTTPStatusError is raised."""
        # Given
        async_client_fixture.get = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def given_request_error__when_get_scraping_jobs__then_return_empty_array__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return empty array when a RequestError is raised."""
        # Given
        async_client_fixture.get = MagicMock(side_effet=RequestError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def given_happy_path__when_download_scraping_job_data__then_return_data__test(
        async_client_fixture: AsyncClient, scraping_job_data_fixture: str
    ) -> None:
        """download_scraping_job_data should return job data on a happy path."""
        # Given
        job_id: str = "job_id"
        response: Response = Response()

        response.text = MagicMock(return_value=scraping_job_data_fixture)
        async_client_fixture.get = AsyncMock(return_value=response)

        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[dict[str, str]] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) != 0

    @staticmethod
    async def given_http_status_error__when_download_scraping_job_data__then_return_empty_array__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """download_scraping_job_data should return empty array when an HTTPStatusError is raised."""
        # Given
        job_id: str = "job_id"
        async_client_fixture.get = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[dict[str, str]] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def given_request_error__when_download_scraping_job_data__then_return_empty_array__test(
        async_client_fixture: AsyncClient,
    ) -> None:
        """download_scraping_job_data should return empty array when a RequestError is raised."""
        # Given
        job_id: str = "job_id"
        async_client_fixture.get = AsyncMock(side_effet=RequestError)
        webscraper: WebScraperIoClient = WebScraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[dict[str, str]] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) == 0
