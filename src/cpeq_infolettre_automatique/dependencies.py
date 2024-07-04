"""Depencies injection functions for the Service class."""

import datetime
from typing import Annotated, Any, cast

import httpx
from decouple import config
from fastapi import Depends
from O365.account import Account
from O365.drive import Folder
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


class OneDriveDependency(ApiDependency):
    """Dependency class for the Singleton O365 Account client."""

    news_folder: Folder

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
        if not account.authenticate():
            raise RuntimeError

        site = account.sharepoint().get_site("baselinequebec.sharepoint.com")
        if site is None:
            raise RuntimeError

        drive = site.site_storage.get_drive(
            "b!fslahRMOAUCsW5P8nXZ3cYwDnL6MT35NpJyHzlyxCgXt0TeRJiWPSb3gQmzCo3t2"
        )
        if drive is None:
            raise RuntimeError

        root_folder: Folder = cast(Folder, drive.get_root_folder())
        news_folder: Folder = cls._get_or_create_subfolder(
            parent_folder=root_folder, folder_name="infolettre_automatique"
        )
        week_folder: Folder = cls._get_or_create_subfolder(
            parent_folder=news_folder,
            folder_name=str(datetime.datetime.now(tz=datetime.UTC).date()),
        )

        cls.news_folder = week_folder

    def __call__(self) -> Folder:
        """Returns the 0365 Account."""
        return self.news_folder

    @classmethod
    def teardown(cls) -> Any:
        """Free resources held by the class."""

    @classmethod
    def _get_or_create_subfolder(cls, parent_folder: Folder, folder_name: str) -> Folder:
        folders = parent_folder.get_child_folders()
        filtered_folders = list(filter(lambda x: x.name == folder_name, folders))
        if len(filtered_folders) == 1:
            return cast(Folder, filtered_folders[0])
        if len(filtered_folders) == 0:
            return cast(Folder, parent_folder.create_child_folder(folder_name))
        raise RuntimeError


def get_webscraperio_client(
    http_client: Annotated[httpx.AsyncClient, Depends(HttpClientDependency())],
) -> WebscraperIoClient:
    """Returns a configured WebscraperIO Client."""
    return WebscraperIoClient(http_client=http_client, api_token=config("WEBSCRAPER_IO_API_KEY"))


def get_news_repository(
    news_folder: Annotated[Folder, Depends(OneDriveDependency())],
) -> NewsRepository:
    """Returns a configured News Repository."""
    return NewsRepository(news_folder)


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
