"""Unit Tests for the Webscraper.io client class."""

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, HTTPStatusError, RequestError, Response
from pydantic import BaseModel

from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


if TYPE_CHECKING:
    from cpeq_infolettre_automatique.schemas import News

# mypy: disable-error-code="method-assign"


class Sitemap(BaseModel):
    sitemap_id: str
    name: str
    url: str


sitemaps: list[Sitemap] = [
    Sitemap(
        name="Ciraig",
        url="https://ciraig.org/index.php/fr/category/actualites/",
        sitemap_id="1127309",
    ),
    Sitemap(
        name="CIRODD",
        url="https://cirodd.org/actualites/",
        sitemap_id="1120854",
    ),
    Sitemap(
        name="FAQDD",
        url="https://faqdd.qc.ca/publications/",
        sitemap_id="1120853",
    ),
    Sitemap(
        name="ECPAR",
        url="http://www.ecpar.org/fr/nouvelles/",
        sitemap_id="1125386",
    ),
]

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


@pytest.fixture(scope="class")
def scraping_job_data_fixture() -> str:
    """Scraping job data fixture."""
    with Path("tests", "unit", "test_data", "scraped_data.txt").open(encoding="utf-8") as file:
        return file.read()


@pytest.fixture(scope="class")
def async_client_fixture() -> AsyncClient:
    """AsyncClient fixture."""
    return AsyncClient()


@pytest.mark.asyncio(scope="class")
class WebscraperIoClientTest:
    """Webscraper.io Client tests."""

    @staticmethod
    async def test_create_scraping_job__when_happy_path__returns_job_id(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return the newly created Job ID on a happy path."""
        # Given
        job_id: str = "job_id"
        response: Response = Response(status_code=200)
        json: Any = {"data": {"id": job_id}}
        response.json = MagicMock(return_value=json)
        async_client_fixture.post = MagicMock(return_value=response)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert return_value == job_id

    @staticmethod
    async def test_create_scraping_job__when_http_status_error__returns_empty_string(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return empty string when an HTTPStatusError is raised."""
        # Given
        async_client_fixture.post = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert not return_value

    @staticmethod
    async def test_create_scraping_job__when_request_error__returns_empty_string(
        async_client_fixture: AsyncClient,
    ) -> None:
        """create_scraping_job should return empty string when a RequestError is raised."""
        # Given
        async_client_fixture.post = AsyncMock(side_effet=RequestError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: str = await webscraper.create_scraping_job("sitemap_id")

        # Then
        assert not return_value

    @staticmethod
    async def test_get_scraping_jobs__when_happy_path__returns_job_ids(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return all the job ids on a happy path."""
        # Given
        job_ids: list[str] = ["1", "2", "3"]
        response: Response = Response(status_code=200)
        json: Any = {"data": [{"id": job_id} for job_id in job_ids]}
        response.json = MagicMock(return_value=json)
        async_client_fixture.get = AsyncMock(return_value=response)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert return_value == job_ids

    @staticmethod
    async def test_get_scraping_jobs__when_http_status_error__returns_empty_array(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return empty array when an HTTPStatusError is raised."""
        # Given
        async_client_fixture.get = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def test_get_scraping_jobs__when_request_error__returns_empty_array(
        async_client_fixture: AsyncClient,
    ) -> None:
        """get_scraping_jobs should return empty array when a RequestError is raised."""
        # Given
        async_client_fixture.get = MagicMock(side_effet=RequestError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: list[str] = await webscraper.get_scraping_jobs()

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def test_download_scraping_job_data__when_happy_path__returns_data(
        async_client_fixture: AsyncClient, scraping_job_data_fixture: str
    ) -> None:
        """download_scraping_job_data should return job data on a happy path."""
        # Given
        job_id: str = "job_id"
        response: Response = Response(status_code=200, text=scraping_job_data_fixture)
        async_client_fixture.get = AsyncMock(return_value=response)

        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: tuple[News, ...] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) != 0

    @staticmethod
    async def test_download_scraping_job_data__when_http_status_error__returns_empty_array(
        async_client_fixture: AsyncClient,
    ) -> None:
        """download_scraping_job_data should return empty array when an HTTPStatusError is raised."""
        # Given
        job_id: str = "job_id"
        async_client_fixture.get = AsyncMock(side_effet=HTTPStatusError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: tuple[News, ...] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) == 0

    @staticmethod
    async def test_download_scraping_job_data__when__request_error__returns_empty_array(
        async_client_fixture: AsyncClient,
    ) -> None:
        """download_scraping_job_data should return empty array when a RequestError is raised."""
        # Given
        job_id: str = "job_id"
        async_client_fixture.get = AsyncMock(side_effet=RequestError)
        webscraper: WebscraperIoClient = WebscraperIoClient(async_client_fixture, "api_key")

        # When
        return_value: tuple[News, ...] = await webscraper.download_scraping_job_data(job_id)

        # Then
        assert len(return_value) == 0
