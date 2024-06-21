"""Configuration for pytest. Add global fixtures here."""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


@pytest.fixture()
def webscraper_io_client_fixture() -> WebScraperIoClient:
    """Fixture for mocked WebScraperIoClient."""
    return AsyncMock(spec=WebScraperIoClient)


@pytest.fixture()
def vectorstore_fixture() -> VectorStore:
    """Fixture for mocked VectorStore."""
    return AsyncMock(spec=VectorStore)


@pytest.fixture()
def news_fixture() -> News:
    """Fixture for a News object."""
    return News(
        title="Some title",
        content="Some content",
        date=datetime(2024, 1, 1),  # noqa: DTZ001
        rubric="Some rubric",
        summary="Some summary",
    )
