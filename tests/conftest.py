"""Configuration for pytest. Add global fixtures here."""

from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest

from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


@pytest.fixture()
def news_fixture() -> News:
    """Fixture for a News object."""
    return News(
        title="Some title",
        content="Some content",
        date=date(2024, 1, 2),
        rubric=None,
        summary=None,
    )


@pytest.fixture()
def webscraper_io_client_fixture(news_fixture: News) -> WebScraperIoClient:
    """Fixture for mocked WebScraperIoClient."""
    webscraper_io_client_fixture = AsyncMock(spec=WebScraperIoClient)
    webscraper_io_client_fixture.get_scraping_jobs = AsyncMock(
        return_value=["job_id_1", "job_id_2"]
    )
    webscraper_io_client_fixture.get_scraping_job_data = AsyncMock(return_value=[news_fixture] * 2)
    return webscraper_io_client_fixture


@pytest.fixture()
def vectorstore_fixture(news_fixture: News) -> VectorStore:
    """Fixture for mocked VectorStore."""
    vectorstore_fixture = AsyncMock(spec=VectorStore)
    vectorstore_fixture.classify_rubric = AsyncMock(return_value="Some rubric")
    vectorstore_fixture.get_examples = AsyncMock(return_value=[news_fixture] * 3)
    return vectorstore_fixture


@pytest.fixture()
def news_repository_fixture() -> Any:
    """Fixture for mocked NewsRepository."""
    return AsyncMock()


@pytest.fixture()
def summary_generator_fixture() -> Any:
    """Fixture for mocked NewsRepository."""
    summary_generator_fixture = AsyncMock()
    summary_generator_fixture.generate_summary = AsyncMock(return_value="Some summary")
    return summary_generator_fixture


@pytest.fixture()
def newsletter_formatter_fixture() -> Any:
    """Fixture for mocked NewsRepository."""
    return AsyncMock()
