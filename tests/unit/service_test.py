"""Tests for service class."""

import datetime as dt
from typing import Any
from unittest.mock import patch

import pytest

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.news_classifier import NewsClassifier
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebscraperIoClient,
    vectorstore_fixture: Vectorstore,
    news_classifier_fixture: NewsClassifier,
    news_repository_fixture: Any,
    summary_generator_fixture: SummaryGenerator,
) -> Service:
    """Fixture for mocked service."""
    service = Service(
        webscraper_io_client=webscraper_io_client_fixture,
        news_repository=news_repository_fixture,
        news_classifier=news_classifier_fixture,
        vectorstore=vectorstore_fixture,
        summary_generator=summary_generator_fixture,
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
        with patch.object(Service, "_prepare_dates") as prepare_dates_mock:
            prepare_dates_mock.return_value = (
                dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
                dt.datetime(2024, 1, 7, tzinfo=dt.UTC),
            )
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
        with patch.object(Service, "_prepare_dates") as prepare_dates_mock:
            prepare_dates_mock.return_value = (
                dt.datetime(2024, 1, 1, tzinfo=dt.UTC),
                dt.datetime(2024, 1, 7, tzinfo=dt.UTC),
            )
            await service_fixture.generate_newsletter()
        assert service_fixture.webscraper_io_client.get_scraping_jobs.called
        assert service_fixture.vectorstore.read_many_by_rubric.called
        assert service_fixture.news_classifier.classify.called
        assert service_fixture.webscraper_io_client.download_scraping_job_data.called
        assert service_fixture.summary_generator.generate.called
        assert service_fixture.webscraper_io_client.delete_scraping_jobs.called
        assert service_fixture.news_repository.create_many_news.called

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
