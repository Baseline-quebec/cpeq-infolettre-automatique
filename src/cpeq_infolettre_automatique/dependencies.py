"""Depencies injection functions for the Service class."""

from typing import Annotated, Any

from decouple import config
from fastapi import Depends
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import VECTORSTORE_CONTENT_FILEPATH
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


def get_webscraper_io_client() -> WebScraperIoClient:
    """Return a WebScraperIoClient instance with the provided API token."""
    return WebScraperIoClient(api_token=config("WEBSCRAPER_IO_API_KEY"))


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
    webscraper_io_client: Annotated[WebScraperIoClient, Depends(get_webscraper_io_client)],
    vectorstore: Annotated[VectorStore, Depends(get_vectorstore)],
) -> Service:
    """Return a Service instance with the provided dependencies."""
    return Service(
        webscraper_io_client=webscraper_io_client,
        news_repository=Any,
        vectorstore=vectorstore,
        summary_generator=Any,
        newsletter_formatter=Any,
    )
