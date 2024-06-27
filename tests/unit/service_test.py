"""Tests for service class."""

from datetime import date, datetime
from typing import Any
from unittest.mock import patch

import pytest

from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


# mypy: disable-error-code="method-assign"
# mypy: disable-error-code="attr-defined"


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebscraperIoClient,
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
    async def test_generate_newsletter__when_happy_path__returns_list_of_news(
        service_fixture: Service,
    ) -> None:
        """Test that the newsletter generation flow and logic operates as intented given expected situation.

        TODO(jsleb333): Remove called assertions with specific tests.
        """
        service_fixture._format_newsletter = lambda news: news
        news_list = await service_fixture.generate_newsletter()
        expected_number_of_news = 4
        assert len(news_list) == expected_number_of_news
        assert service_fixture.webscraper_io_client.get_scraping_jobs.called
        assert service_fixture.webscraper_io_client.download_scraping_job_data.called
        assert service_fixture.vectorstore.classify_rubric.called
        assert service_fixture.vectorstore.get_examples.called
        assert service_fixture.summary_generator.generate_summary.called
        assert service_fixture.webscraper_io_client.delete_scraping_jobs.called
        assert service_fixture.news_repository.save_news.called

    @staticmethod
    def test_prepare_dates__when_default_args__returns_closest_monday_to_monday_period() -> None:
        """Test that the start and end dates are correctly prepared when no arguments are provided."""
        with patch("cpeq_infolettre_automatique.service.datetime") as datetime_mock:
            datetime_mock.now.return_value = datetime(2024, 1, 9)  # noqa: DTZ001
            start_date, end_date = Service._prepare_dates()
            first_monday = date(2024, 1, 1)
            second_monday = date(2024, 1, 8)
            assert start_date == first_monday
            assert end_date == second_monday
