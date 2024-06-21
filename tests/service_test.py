"""Tests for service class."""

from unittest.mock import AsyncMock

import pytest

from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


@pytest.fixture()
def service_fixture(
    webscraper_io_client_fixture: WebScraperIoClient, vectorstore_fixture: VectorStore
) -> Service:
    """Fixture for mocked service."""
    service = Service(
        webscraper_io_client=webscraper_io_client_fixture,
        news_repository=AsyncMock(),
        vectorstore=vectorstore_fixture,
        summary_generator=AsyncMock(),
        newsletter_formatter=AsyncMock(),
    )
    return service


class TestService:
    """Test the Service class."""

    @staticmethod
    @pytest.mark.asyncio()
    async def test_generate_newsletter(
        service_fixture: Service,
    ) -> None:
        """Test generating a newsletter."""
