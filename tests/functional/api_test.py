"""Test cpeq-infolettre-automatique REST API."""

from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from O365.drive import Folder
from typeguard import suppress_type_checks

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
def client_fixture(
    service_fixture: Service, onedrive_fixture: OneDriveDependency
) -> Generator[TestClient, None, None]:
    """Create a TestClient instance with a mock Bot and ChatHistoryDB instances."""

    class DependencyPatch:
        """Patch dependencies to return mocked dependencies."""

        def get(self, key: Any, default: Any) -> Any:  # noqa: PLR6301
            """Return mocked dependencies when needed.

            Both 'key' and 'default' refers to the same function used in Depends.
            See fastapi.dependencies.utils.py in the function 'solve_dependencies' for the call to 'get'.
            """
            if key == get_vectorstore:
                return AsyncMock()
            if key == get_webscraperio_client:
                return AsyncMock()
            if key == get_service:
                return service_fixture
            if isinstance(key, OneDriveDependency):
                return onedrive_fixture
            return default

    app.dependency_overrides = DependencyPatch()  # type: ignore[assignment]

    # Patch lifespan context
    @asynccontextmanager
    async def _lifespan(_: FastAPI) -> AsyncIterator[None]:  # noqa: RUF029
        yield

    app.router.lifespan_context = _lifespan

    # Create TestClient instance, suppressing Typeguard's type check because the dependency overrides change the type of the dependencies
    with suppress_type_checks(), TestClient(app) as client:
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
    expected_message = "Newsletter generation started."

    response = client_fixture.get("/generate-newsletter")
    assert response.status_code == SUCCESS_HTTP_STATUS_CODE
    assert response.text == expected_message
    assert service_fixture.generate_newsletter.called
