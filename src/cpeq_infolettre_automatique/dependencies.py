"""Depencies injection functions for the Service class."""

import datetime
from typing import Annotated, Any

import httpx
from decouple import config
from fastapi import Depends
from O365.account import Account
from O365.drive import Drive
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import VECTORSTORE_CONTENT_FILEPATH
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


class ApiDependency:
    """A base class for FastAPI dependency injection. Any dependency should redefine some or all the methods of this class."""

    @classmethod
    def setup(cls) -> None:
        """Create the global resources of the dependency. Call this method at app startup in `lifespan`."""

    def __init__(self) -> None:
        """Create a new instance of the dependency.

        Will be called by FastAPI when the dependency is injected with Depends(). The instanciated ApiDependency object should define __call__ to return the dependency to inject.

        Any subdependencies used by the dependency should be injected here, in the __init__ method.
        """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Initialize if needed, and then return the dependency to inject. Can act as a factory."""

    @classmethod
    def teardown(cls) -> Any:
        """Clean up the global resources of the dependency. Call this method at app takedown in `lifespan`."""


class HttpClientDependency(ApiDependency):
    """Dependency class for the Singleton HTTP Client."""

    client: httpx.AsyncClient

    @classmethod
    def setup(cls) -> None:
        """Setup dependency."""
        cls.client = httpx.AsyncClient(http2=True)

    def __call__(self) -> httpx.AsyncClient:
        """Returns the HTTP Client instance."""
        return self.client

    @classmethod
    async def teardown(cls) -> Any:
        """Free resources held by the class."""
        await cls.client.aclose()


class OneDriveFolderDependency(ApiDependency):
    """Dependency class for the Singleton O365 Account client."""

    drive: Drive
    folder_name: str

    @classmethod
    def setup(cls) -> None:
        """Setup dependency."""
        credentials = (
            "99536437-db80-4ece-8bd5-0f4e4b1cba22",
            "zfv8Q~U.AUmeoEDQpuEqTHsBvEnrw2TUXbqo5aLn",
        )
        account = Account(
            credentials,
            auth_flow_type="credentials",
            tenant_id="0e86b3e2-6171-44c5-82da-e974b48c0c3a",
        )
        account.authenticate(scopes=["basic", "onedrive_all"])
        drive: Drive | None = account.storage().get_default_drive()

        if drive is None:
            raise RuntimeError

        cls.folder_name = str(datetime.datetime.now(tz=datetime.UTC).date())

    def __call__(self) -> tuple[Drive, str]:
        """Returns the 0365 Account."""
        return (self.drive, self.folder_name)

    @classmethod
    def teardown(cls) -> Any:
        """Free resources held by the class."""


def get_webscraperio_client(
    http_client: Annotated[httpx.AsyncClient, Depends(HttpClientDependency())],
) -> WebscraperIoClient:
    """Returns a configured WebscraperIO Client."""
    return WebscraperIoClient(http_client=http_client, api_token=config("WEBSCRAPER_IO_API_KEY"))


def get_news_repository(
    drive_info: Annotated[tuple[Drive, str], Depends(OneDriveFolderDependency())],
) -> NewsRepository:
    """Returns a configured News Repository."""
    return NewsRepository(drive_info[0], drive_info[1])


def get_openai_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI instance with the provided API key."""
    return AsyncOpenAI(api_key=config("OPENAI_API_KEY"))


def get_vectorstore(
    openai_client: Annotated[AsyncOpenAI, Depends(get_openai_client)],
) -> VectorStore:
    """Return a VectorStore instance with the provided content filepath."""
    return VectorStore(
        client=openai_client,
        filepath=VECTORSTORE_CONTENT_FILEPATH.as_posix(),
    )


def get_service(
    webscraper_io_client: Annotated[WebscraperIoClient, Depends(get_webscraperio_client)],
    vectorstore: Annotated[VectorStore, Depends(get_vectorstore)],
    news_repository: Annotated[NewsRepository, Depends(get_news_repository)],
) -> Service:
    """Return a Service instance with the provided dependencies."""
    return Service(
        webscraper_io_client=webscraper_io_client,
        news_repository=news_repository,
        vectorstore=vectorstore,
        summary_generator=Any,
        newsletter_formatter=Any,
    )
