"""Configuration for pytest. Add global fixtures here."""

import datetime as dt
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import weaviate

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.reference_news_repository import (
    ReferenceNewsRepository,
)
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def news_fixture() -> News:
    """Fixture for a News object."""
    return News(
        title="Some title",
        content="Some content",
        datetime=dt.datetime(2024, 1, 2, tzinfo=dt.UTC),
        rubric=None,
        summary=None,
    )


@pytest.fixture()
def reference_news_fixture(news_fixture: News) -> News:
    """Fixture for a News object."""
    news = news_fixture.model_dump()
    news["rubric"] = Rubric.BIODIVERSITE_MILIEUX_HUMIDES_ET_ESPECES_EN_PERIL
    news["summary"] = "Some summary"
    reference_news = News(**news)
    return reference_news


@pytest.fixture()
def webscraper_io_client_fixture(news_fixture: News) -> WebscraperIoClient:
    """Fixture for mocked WebScraperIoClient."""
    webscraper_io_client_fixture = AsyncMock(spec=WebscraperIoClient)
    webscraper_io_client_fixture.get_scraping_jobs = AsyncMock(
        return_value=["job_id_1", "job_id_2"]
    )
    webscraper_io_client_fixture.download_scraping_job_data = AsyncMock(
        return_value=[news_fixture] * 2
    )
    return webscraper_io_client_fixture


@pytest.fixture()
def test_collection_name() -> str:
    """Fixture for the collection name."""
    return "Test_collection"


@pytest.fixture()
def vectorstore_client_fixture(
    test_collection_name: str,
) -> Iterator[weaviate.WeaviateClient]:
    """Fixture for mocked Weaviate client."""
    client: weaviate.WeaviateClient = weaviate.connect_to_embedded()
    if not client.is_ready():
        error_msg = "Vectorstore is not ready"
        raise ValueError(error_msg)
    yield client
    client.collections.delete(test_collection_name)
    client.close()


@pytest.fixture()
def vectorstore_config_fixture(test_collection_name: str) -> VectorstoreConfig:
    """Fixture for VectorstoreConfig."""
    return VectorstoreConfig(
        collection_name=test_collection_name,
        batch_size=10,
        concurrent_requests=5,
    )


@pytest.fixture()
def vectorstore_fixture() -> Vectorstore:
    """Fixture for mocked Vectorstore."""
    vectorstore_fixture = MagicMock(spec=Vectorstore)
    vectorstore_fixture.classify_news_rubric = AsyncMock(
        return_value=Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
    )
    return vectorstore_fixture


@pytest.fixture()
def news_repository_fixture() -> Any:
    """Fixture for mocked NewsRepository."""
    news_repository_fixture = AsyncMock()
    news_repository_fixture.create = AsyncMock()
    return news_repository_fixture


@pytest.fixture()
def reference_news_repository_fixture(reference_news_fixture: News) -> Any:
    """Fixture for mocked ReferenceNewsRepository."""
    reference_news_repository_fixture = MagicMock(spec=ReferenceNewsRepository)
    reference_news_repository_fixture.read_many_by_rubric = AsyncMock(
        return_value=[reference_news_fixture]
    )
    return reference_news_repository_fixture


@pytest.fixture()
def newsletter_repository_fixture() -> Any:
    """Fixture for mocked NewsletterRepository."""
    newsletter_repository_fixture = AsyncMock()
    newsletter_repository_fixture.create = AsyncMock()
    return newsletter_repository_fixture


@pytest.fixture()
def summary_generator_fixture() -> Any:
    """Fixture for mocked SummaryGenerator."""
    summary_generator_fixture = AsyncMock()
    summary_generator_fixture.generate_summary = AsyncMock(return_value="Some summary")
    return summary_generator_fixture


@pytest.fixture()
def newsletter_formatter_fixture() -> Any:
    """Fixture for mocked NewsLetterFormater."""
    return MagicMock()
