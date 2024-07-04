"""Tests for service class."""

import datetime as dt
from typing import Any
from unittest.mock import patch

import pytest

from cpeq_infolettre_automatique.reference_news_repository import ReferenceNewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebscraperIoClient,
    vectorstore_fixture: Vectorstore,
    reference_news_repository_fixture: ReferenceNewsRepository,
    news_repository_fixture: Any,
    newsletter_repository_fixture: Any,
    summary_generator_fixture: SummaryGenerator,
    newsletter_formatter_fixture: Any,
) -> Service:
    """Fixture for mocked service."""
    service = Service(
        webscraper_io_client=webscraper_io_client_fixture,
        news_repository=news_repository_fixture,
        reference_news_repository=reference_news_repository_fixture,
        newsletter_repository=newsletter_repository_fixture,
        vectorstore=vectorstore_fixture,
        summary_generator=summary_generator_fixture,
        newsletter_formatter=newsletter_formatter_fixture,
    )
    service._prepare_dates = lambda *_: (
        dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
        dt.datetime(2024, 1, 7, tzinfo=dt.UTC),
    )
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
        assert service_fixture.vectorstore.classify_news_rubric.called
        assert service_fixture.reference_news_repository.read_many_by_rubric.called
        assert service_fixture.webscraper_io_client.download_scraping_job_data.called
        assert service_fixture.summary_generator.generate.called
        assert service_fixture.webscraper_io_client.delete_scraping_jobs.called
        assert service_fixture.news_repository.create.called

    @staticmethod
    def test_prepare_dates__when_default_args__returns_closest_monday_to_monday_period() -> None:
        """Test that the start and end dates are correctly prepared when no arguments are provided."""
        with patch(
            "cpeq_infolettre_automatique.service.get_current_montreal_datetime"
        ) as get_current_datetime_mock:
            get_current_datetime_mock.return_value = dt.datetime(2024, 1, 9, tzinfo=dt.UTC)
            start_date, end_date = Service._prepare_dates()
            first_monday = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
            second_monday = dt.datetime(2024, 1, 8, tzinfo=dt.UTC)
            assert start_date == first_monday
            assert end_date == second_monday
