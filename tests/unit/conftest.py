"""Configuration for pytest. Add global fixtures here."""

import datetime as dt
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import weaviate
from pydantic_core import Url

from cpeq_infolettre_automatique.completion_model import CompletionModel
from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.reference_news_repository import (
    ReferenceNewsRepository,
)
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def news_fixture() -> News:
    """Fixture for a News object."""
    return News(
        title="Some title",
        content="Some content",
        link=Url("https://somelink.com"),
        datetime=dt.datetime(2024, 1, 2, tzinfo=dt.UTC),
        rubric=None,
        summary=None,
    )


@pytest.fixture()
def classified_news_fixture(news_fixture: News) -> News:
    """Fixture for a News object with a classification."""
    classified_news = news_fixture.model_copy()
    classified_news.rubric = Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME
    return classified_news


@pytest.fixture()
def summarized_news_fixture(classified_news_fixture: News) -> News:
    """Fixture for a News object with a summary."""
    summarized_news = classified_news_fixture.model_copy()
    summarized_news.summary = "Some summary"
    return summarized_news


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
        nb_items_retrieved=2,
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
    news_repository_fixture = MagicMock()
    news_repository_fixture.create_news = MagicMock()
    news_repository_fixture.create_newsletter = MagicMock()
    return news_repository_fixture


@pytest.fixture()
def reference_news_repository_fixture(summarized_news_fixture: News) -> Any:
    """Fixture for mocked ReferenceNewsRepository."""
    reference_news_repository_fixture = MagicMock(spec=ReferenceNewsRepository)
    reference_news_repository_fixture.read_many_by_rubric.return_value = [summarized_news_fixture]
    return reference_news_repository_fixture


@pytest.fixture()
def newsletter_formatter_fixture() -> Any:
    """Fixture for mocked NewsLetterFormater."""
    return MagicMock()


@pytest.fixture()
def summary_generator_fixture() -> SummaryGenerator:
    """Fixture for the SummaryGenerator."""
    completion_model_mock = MagicMock(spec=CompletionModel)
    summary_generator_fixture = SummaryGenerator(completion_model=completion_model_mock)
    summary_generator_fixture.generate = AsyncMock(return_value="This is a summary")
    return summary_generator_fixture
