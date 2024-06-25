"""Tests for service class."""

from datetime import date
from typing import Any

import pytest

from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebScraperIoClient,
    vectorstore_fixture: VectorStore,
    news_repository_fixture: Any,
    summary_generator_fixture: Any,
    newsletter_formatter_fixture: Any,
) -> Service:
    """Fixture for mocked service."""
    service = Service(
        webscraper_io_client=webscraper_io_client_fixture,
        news_repository=news_repository_fixture,
        vectorstore=vectorstore_fixture,
        summary_generator=summary_generator_fixture,
        newsletter_formatter=newsletter_formatter_fixture,
    )
    service._prepare_dates = lambda *_: (date(2024, 1, 1), date(2024, 1, 7))
    return service


class TestService:
    """Test the Service class."""

    @staticmethod
    @pytest.mark.asyncio()
    async def generate_newsletter__given_happy_path__returns_list_of_news(
        service_fixture: Service,
    ) -> None:
        """Test that the newsletter generation flow and logic operates as intented given expected situation."""
        service_fixture._format_newsletter = lambda news: news  # type: ignore[return-value, assignment]
        news_list = await service_fixture.generate_newsletter()
        expected_number_of_news = 4
        assert len(news_list) == expected_number_of_news
        assert service_fixture.webscraper_io_client.get_scraping_jobs.called
        assert service_fixture.webscraper_io_client.get_scraping_job_data.called
        assert service_fixture.vectorstore.classify_rubric.called
        assert service_fixture.vectorstore.get_examples.called
        assert service_fixture.summary_generator.generate_summary.called
        assert service_fixture.webscraper_io_client.delete_scraping_jobs.called
        assert service_fixture.repository.save_news.called
