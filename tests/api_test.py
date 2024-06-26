"""Test cpeq-infolettre-automatique REST API."""

from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi.testclient import TestClient

from cpeq_infolettre_automatique.api import app
from cpeq_infolettre_automatique.dependencies import (
    get_service,
    get_vectorstore,
    get_webscraper_io_client,
)
from cpeq_infolettre_automatique.service import Service


EXPECTED_NEWSLETTER = "Some newsletter"
SUCCESS_HTTP_STATUS_CODE = 200


@pytest.fixture(scope="session")
def service_fixture() -> Service:
    """Fixture for mocked service."""
    service_mock = AsyncMock()
    service_mock.generate_newsletter.return_value = EXPECTED_NEWSLETTER
    return service_mock


@pytest.fixture(scope="session")
def client_fixture(service_fixture: Service) -> TestClient:
    """Create a test client for the FastAPI app."""
    app.dependency_overrides[get_vectorstore] = AsyncMock()
    app.dependency_overrides[get_webscraper_io_client] = AsyncMock()
    app.dependency_overrides[get_service] = lambda: service_fixture
    return TestClient(app)


def test_root_status_code() -> None:
    """Test that reading the root is successful."""
    if not httpx.codes.is_success(SUCCESS_HTTP_STATUS_CODE):
        error_message = "Status code should indicate success"
        raise AssertionError(error_message)


def test_generate_newsletter__(
    client_fixture: TestClient,
    service_fixture: Service,
) -> None:
    """Test generating a newsletter."""
    response = client_fixture.get("/generate-newsletter")
    assert response.status_code == SUCCESS_HTTP_STATUS_CODE
    assert response.text == EXPECTED_NEWSLETTER
    assert service_fixture.generate_newsletter.called
