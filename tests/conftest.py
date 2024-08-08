"""Configuration for pytest. Add global fixtures here."""

import datetime as dt
from collections.abc import Iterator
from inspect import cleandoc
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import weaviate
from pydantic_core import Url

from cpeq_infolettre_automatique.completion_model import CompletionModel
from cpeq_infolettre_automatique.config import Relevance, Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.news_classifier import (
    NewsRelevancyClassifier,
    NewsRubricClassifier,
)
from cpeq_infolettre_automatique.news_producer import NewsProducer
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import News, Newsletter
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def news_fixture() -> News:
    """Fixture for a News object."""
    return News(
        title="Some title",
        content="Some content",
        link=Url("https://somelink.com/"),
        datetime=dt.datetime(2024, 1, 2, tzinfo=dt.UTC),
        rubric=None,
        summary=None,
        job_id="job_id_1",
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
def multiple_summarized_news_fixture(summarized_news_fixture: News) -> list[News]:
    """Fixture for a News object with a summary."""
    summarized_news_fixture_copy_1 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_1.rubric = (
        Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
    )
    summarized_news_fixture_copy_1.title = "Title 1"
    summarized_news_fixture_copy_1.summary = "Summary 1"
    summarized_news_fixture_copy_2 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_2.rubric = Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME
    summarized_news_fixture_copy_2.title = "Title 2"
    summarized_news_fixture_copy_2.summary = "Summary 2"
    summarized_news_fixture_copy_3 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_3.rubric = (
        Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
    )
    summarized_news_fixture_copy_3.title = "Title 3"
    summarized_news_fixture_copy_3.summary = "Summary 3"
    summarized_news = [
        summarized_news_fixture_copy_1,
        summarized_news_fixture_copy_2,
        summarized_news_fixture_copy_3,
    ]

    return summarized_news


@pytest.fixture()
def multiple_summarized_news_with_unclassified_rubric_fixture(
    summarized_news_fixture: News,
) -> list[News]:
    """Fixture for a News object with a summary."""
    summarized_news_fixture_copy_1 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_1.rubric = (
        Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
    )
    summarized_news_fixture_copy_1.title = "Title 1"
    summarized_news_fixture_copy_1.summary = "Summary 1"

    summarized_news_fixture_copy_2 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_2.rubric = None
    summarized_news_fixture_copy_2.title = "Title 2"
    summarized_news_fixture_copy_2.summary = "Summary 2"

    summarized_news_fixture_copy_3 = summarized_news_fixture.model_copy()
    summarized_news_fixture_copy_3.rubric = Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME
    summarized_news_fixture_copy_3.title = "Title 3"
    summarized_news_fixture_copy_3.summary = "Summary 3"

    summarized_news = [
        summarized_news_fixture_copy_1,
        summarized_news_fixture_copy_2,
        summarized_news_fixture_copy_3,
    ]

    return summarized_news


@pytest.fixture(scope="session")
def newsletter_fixture() -> Newsletter:
    """Fixture for a Newsletter object."""
    start_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    end_datetime = dt.datetime(2024, 1, 7, tzinfo=dt.UTC)
    expected_newsletter_content = cleandoc(
        f"""# Infolettre du CPEQ


            Date de publication: {end_datetime.date()}


            Voici les nouvelles de la semaine du {start_datetime.date()} au {end_datetime.date()}.

            ## {Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE.value}

            ### Title 1

            Summary 1

            Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/).

            ### Title 3

            Summary 3

            Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/).

            ## {Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME.value}

            ### Title 2

            Summary 2

            Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/)."""
    )

    newsletter = MagicMock(spec=Newsletter)
    newsletter.to_markdown.return_value = expected_newsletter_content
    return newsletter


@pytest.fixture()
def newsletter_fixture_with_unclassified_rubric() -> Newsletter:
    """Fixture for a Newsletter object."""
    start_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    end_datetime = dt.datetime(2024, 1, 7, tzinfo=dt.UTC)
    expected_newsletter_content = cleandoc(
        f"""# Infolettre du CPEQ


               Date de publication: {end_datetime.date()}


               Voici les nouvelles de la semaine du {start_datetime.date()} au {end_datetime.date()}.

               ## {Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE.value}

               ### Title 1

               Summary 1

               Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/).

               ## {Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME.value}

               ### Title 3

               Summary 3

               Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/).

               ## {Rubric.AUTRE.value}

               ### Title 2

               Summary 2

               Pour en connaître davantage, nous vous invitons à consulter cet [hyperlien](https://somelink.com/)."""
    )

    newsletter = MagicMock(spec=Newsletter)
    newsletter.to_markdown.return_value = expected_newsletter_content
    return newsletter


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
    """Fixture for mocked Weaviate client.

    Raises:
        ValueError: If the vectorstore is not ready.
    """
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
        max_nb_items_retrieved=2,
        minimal_score=0.0,
        hybrid_weight=1.00,
    )


@pytest.fixture()
def rubric_classification_fixture() -> Rubric:
    """Fixture for a Rubric classification."""
    return Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE


@pytest.fixture()
def embedding_model_fixture() -> EmbeddingModel:
    """Fixture for a mocked EmbeddingModel."""
    embedding_model_fixture = MagicMock(spec=EmbeddingModel)
    embedding_model_fixture.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
    return embedding_model_fixture


@pytest.fixture()
def vectorstore_fixture(summarized_news_fixture: News) -> Vectorstore:
    """Fixture for mocked Vectorstore."""
    vectorstore_fixture = MagicMock(spec=Vectorstore)
    vectorstore_fixture.search_similar_news.return_value = [summarized_news_fixture]
    return vectorstore_fixture


@pytest.fixture()
def news_repository_fixture() -> NewsRepository:
    """Fixture for mocked NewsRepository."""
    news_repository_fixture = MagicMock()
    news_repository_fixture.create_news = MagicMock()
    news_repository_fixture.create_many_news = MagicMock()
    news_repository_fixture.create_newsletter = MagicMock()
    return news_repository_fixture


@pytest.fixture()
def news_rubric_classifier_fixture(rubric_classification_fixture: Rubric) -> Any:
    """Fixture for mocked ReferenceNewsRepository."""
    news_rubric_classifier_fixture = MagicMock(spec=NewsRubricClassifier)
    news_rubric_classifier_fixture.predict = AsyncMock(return_value=rubric_classification_fixture)
    return news_rubric_classifier_fixture


@pytest.fixture()
def completion_model_fixture() -> CompletionModel:
    """Fixture for a mocked completion model."""
    completion_model_fixture = MagicMock(spec=CompletionModel)
    completion_model_fixture.complete_message = AsyncMock(return_value="This is a summary")
    return completion_model_fixture


@pytest.fixture()
def summary_generator_fixture(
    completion_model_fixture: CompletionModel,
    vectorstore_fixture: Vectorstore,
) -> SummaryGenerator:
    """Fixture for the SummaryGenerator."""
    summary_generator_config = MagicMock()
    return SummaryGenerator(
        completion_model_fixture, vectorstore_fixture, summary_generator_config
    )


@pytest.fixture()
def news_producer_fixture(
    summary_generator_fixture: SummaryGenerator,
    news_rubric_classifier_fixture: NewsRubricClassifier,
) -> NewsProducer:
    """Fixture for the NewsProducer."""
    news_producer_fixture = NewsProducer(
        summary_generator=summary_generator_fixture,
        news_rubric_classifier=news_rubric_classifier_fixture,
    )
    news_producer_fixture.produce_news = AsyncMock(side_effect=news_producer_fixture.produce_news)
    return news_producer_fixture


@pytest.fixture()
def news_relevance_classifier_fixture() -> NewsRelevancyClassifier:
    """Fixture for the NewsRelevancyClassifier."""
    news_relevance_classifier_fixture = MagicMock(spec=NewsRelevancyClassifier)
    news_relevance_classifier_fixture.predict = AsyncMock(return_value=Relevance.PERTINENT)
    return news_relevance_classifier_fixture
