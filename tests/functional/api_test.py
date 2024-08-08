"""Test cpeq-infolettre-automatique REST API."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from cpeq_infolettre_automatique.api import app
from cpeq_infolettre_automatique.dependencies import (
    OneDriveDependency,
    get_service,
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
def client_fixture(service_fixture: Service) -> Iterator[TestClient]:
    """Create a test client for the FastAPI app."""
    app.dependency_overrides[get_service] = lambda: service_fixture
    app.dependency_overrides[OneDriveDependency.get_folder_name] = (
        lambda: "news_folder/week_folder"
    )
    # Patch lifespan context

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: RUF029, ARG001
        yield

    app.router.lifespan_context = _lifespan

    # Create TestClient instance, suppressing Typeguard's type check because the dependency overrides change the type of the dependencies
    with TestClient(app) as client:
        yield client
        app.dependency_overrides = {}


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
    expected_folder_name = "news_folder/week_folder."

    response = client_fixture.get("/generate-newsletter")
    assert response.status_code == SUCCESS_HTTP_STATUS_CODE
    assert expected_folder_name in response.text
    assert service_fixture.generate_newsletter.called
