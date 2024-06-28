"""Depencies injection functions for the Service class."""

from typing import Annotated, Any

import httpx
import weaviate
from decouple import config
from fastapi import Depends
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel, OpenAIEmbeddingModel
from cpeq_infolettre_automatique.reference_news_repository import ReferenceNewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore, get_vectorstore_client
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


def get_webscraperio_client(
    http_client: Annotated[httpx.AsyncClient, Depends(HttpClientDependency())],
) -> WebscraperIoClient:
    """Returns a configured WebscraperIO Client."""
    return WebscraperIoClient(http_client=http_client, api_token=config("WEBSCRAPER_IO_API_KEY"))


def get_openai_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI instance with the provided API key."""
    return AsyncOpenAI(api_key=config("OPENAI_API_KEY"))


def get_embedding_model(
    openai_client: Annotated[AsyncOpenAI, Depends(get_openai_client)],
) -> EmbeddingModel:
    """Return an EmbeddingModel instance with the provided API key."""
    return OpenAIEmbeddingModel(client=openai_client)


def get_vectorstore(
    vectorstore_client: Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)],
    embedding_model: Annotated[EmbeddingModel, Depends(get_embedding_model)],
) -> VectorStore:
    """Return a VectorStore instance with the provided dependencies."""
    Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)]
    return VectorStore(client=vectorstore_client, embedding_model=embedding_model)


def get_reference_news_repository(
    vectorstore_client: Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)],
) -> ReferenceNewsRepository:
    """Return a ReferenceNewsRepository instance."""
    return ReferenceNewsRepository(
        client=vectorstore_client, collection_name=VectorstoreConfig.collection_name
    )


def get_service(
    webscraper_io_client: Annotated[WebscraperIoClient, Depends(get_webscraperio_client)],
    vectorstore: Annotated[VectorStore, Depends(get_vectorstore)],
    reference_news_repository: Annotated[
        ReferenceNewsRepository, Depends(get_reference_news_repository)
    ],
) -> Service:
    """Return a Service instance with the provided dependencies."""
    return Service(
        webscraper_io_client=webscraper_io_client,
        news_repository=Any,
        reference_news_repository=reference_news_repository,
        newsletter_repository=Any,
        vectorstore=vectorstore,
        summary_generator=Any,
        newsletter_formatter=Any,
    )
