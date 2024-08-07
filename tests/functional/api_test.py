"""Test cpeq-infolettre-automatique REST API."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from O365.drive import Folder

from cpeq_infolettre_automatique.api import app
from cpeq_infolettre_automatique.dependencies import (
    OneDriveDependency,
    get_service,
    get_vectorstore,
    get_webscraperio_client,
)
from cpeq_infolettre_automatique.schemas import Newsletter
from cpeq_infolettre_automatique.service import Service


SUCCESS_HTTP_STATUS_CODE = 200


@pytest.fixture(scope="session")
def service_fixture(newsletter_fixture: Newsletter) -> Service:
    """Fixture for mocked service."""
    service_mock = AsyncMock()
    service_mock.generate_newsletter = AsyncMock(return_value=newsletter_fixture)
    return service_mock


@pytest.fixture(scope="session")
def onedrive_fixture() -> OneDriveDependency:
    """Fixture for OneDrive."""
    onedrive_fixture = MagicMock(spec=OneDriveDependency)
    onedrive_fixture.news_folder = MagicMock(spec=Folder)
    onedrive_fixture.week_folder = MagicMock(spec=Folder)
    return onedrive_fixture


@pytest.fixture(scope="session")
def client_fixture(service_fixture: Service, onedrive_fixture: OneDriveDependency) -> TestClient:
    """Create a test client for the FastAPI app."""
    app.dependency_overrides[get_vectorstore] = AsyncMock()
    app.dependency_overrides[get_webscraperio_client] = AsyncMock()
    app.dependency_overrides[get_service] = lambda: service_fixture
    app.dependency_overrides[OneDriveDependency()] = onedrive_fixture
    return TestClient(app)


def test_root_status_code() -> None:
    """Test that reading the root is successful.

    Raises:
        AssertionError: If the status code is not successful.
    """
    if not httpx.codes.is_success(SUCCESS_HTTP_STATUS_CODE):
        error_message = "Status code should indicate success"
        raise AssertionError(error_message)


def test_generate_newsletter__when_happy_path__returns_successful_response(
    client_fixture: TestClient, service_fixture: Service
) -> None:
    """Test generating a newsletter."""
    expected_message = "Newsletter generation started."

    response = client_fixture.get("/generate-newsletter")
    assert response.status_code == SUCCESS_HTTP_STATUS_CODE
    assert response.text == expected_message
    assert service_fixture.generate_newsletter.called
