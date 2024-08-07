"""Tests for service class."""

import datetime as dt

import pytest

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.news_classifier import NewsRelevancyClassifier
from cpeq_infolettre_automatique.news_producer import NewsProducer
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebscraperIoClient,
    news_repository_fixture: NewsRepository,
    news_producer_fixture: NewsProducer,
    news_relevance_classifier_fixture: NewsRelevancyClassifier,
) -> Service:
    """Fixture for mocked service.

    Returns:
        The mocked Service.
    """
    service = Service(
        start_date=dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        end_date=dt.datetime(2024, 1, 7, tzinfo=dt.UTC),
        webscraper_io_client=webscraper_io_client_fixture,
        news_repository=news_repository_fixture,
        news_producer=news_producer_fixture,
        news_relevancy_classifier=news_relevance_classifier_fixture,
    )
    return service


class TestService:
    """Test the Service class."""

    @staticmethod
    @pytest.mark.asyncio()
    async def test_generate_newsletter__when_provided_with_news__returns_proper_newsletter(
        service_fixture: Service,
        news_fixture: News,
        rubric_classification_fixture: Rubric,
    ) -> None:
        """Test that the generate_newsletter outputs newsletter with proper content."""
        newsletter = await service_fixture.generate_newsletter()
        newsletter_content = newsletter.to_markdown()
        assert rubric_classification_fixture.value in newsletter_content
        assert news_fixture.title in newsletter_content

    @staticmethod
    @pytest.mark.asyncio()
    async def test_generate_newsletter__when_happy_path__all_subservices_are_called(
        service_fixture: Service,
    ) -> None:
        """Test that the newsletter generation flow and logic operates as intented given expected situation.

        TODO(jsleb333): Remove called assertions with specific tests.
        """
        await service_fixture.generate_newsletter()
        assert service_fixture.webscraper_io_client.get_scraping_jobs.called
        assert service_fixture.news_relevancy_classifier.predict.called
        assert service_fixture.webscraper_io_client.download_scraping_job_data.called
        assert service_fixture.news_producer.produce_news.called
        assert service_fixture.webscraper_io_client.delete_scraping_jobs.called
        assert service_fixture.news_repository.create_many_news.called
