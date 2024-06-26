"""Depencies injection functions for the Service class."""

from typing import Annotated, Any

import weaviate
from decouple import config
from fastapi import Depends
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.embedding_model import EmbeddingModel, OpenAIEmbeddingModel
from cpeq_infolettre_automatique.news_repository import NewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore, get_vectorstore_client
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


def get_webscraper_io_client() -> WebScraperIoClient:
    """Return a WebScraperIoClient instance with the provided API token."""
    return WebScraperIoClient(api_token=config("WEBSCRAPER_IO_API_KEY"))


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
) -> VectorStore:
    """Return a VectorStore instance with the provided dependencies."""
    Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)]
    return VectorStore(client=vectorstore_client)


def get_news_repository(
    vectorstore_client: Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)],
    embedding_model: Annotated[EmbeddingModel, Depends(get_embedding_model)],
) -> NewsRepository:
    """Return a NewsRepository instance."""
    return NewsRepository(client=vectorstore_client, embedding_model=embedding_model)


def get_service(
    webscraper_io_client: Annotated[WebScraperIoClient, Depends(get_webscraper_io_client)],
    vectorstore: Annotated[VectorStore, Depends(get_vectorstore)],
    news_repository: Annotated[NewsRepository, Depends(get_news_repository)],
) -> Service:
    """Return a Service instance with the provided dependencies."""
    return Service(
        webscraper_io_client=webscraper_io_client,
        news_repository=news_repository,
        newsletter_repository=Any,
        vectorstore=vectorstore,
        summary_generator=Any,
        newsletter_formatter=Any,
    )
