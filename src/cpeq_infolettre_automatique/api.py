"""cpeq-infolettre-automatique REST API."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import coloredlogs
from decouple import config
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse, Response

from cpeq_infolettre_automatique.dependencies import (
    HttpClientDependency,
    OneDriveDependency,
    get_service,
    get_webscraperio_client,
)
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Handle FastAPI startup and shutdown events."""
    # Startup events:
    # - Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    # Add coloredlogs' coloured StreamHandler to the root logger.
    # - Add coloredlogs' colored StreamHandler to the root logger.
    coloredlogs.install()

    HttpClientDependency.setup()
    OneDriveDependency.setup()

    yield

    # Shutdown events.
    await HttpClientDependency.teardown()


app = FastAPI(lifespan=lifespan)


@app.post("/initiate_scraping/{sitemap_id}")
async def initiate_scraping(
    sitemap_id: str,
    webscraper_client: Annotated[WebscraperIoClient, Depends(get_webscraperio_client)],
) -> str:
    """Initiate web scraping jobs and process their data.

    Returns:
        list[tuple[str, str]]: A list of tuples associating a sitemap id to a job id
    """
    return await webscraper_client.create_scraping_job(sitemap_id=sitemap_id)


@app.get("/get-articles")
def get_articles_from_scraper() -> JSONResponse:
    """Retrieve and return articles.

    Returns:
        JSONResponse: An empty articles list response.
    """
    # Appeler l'API de webscraper.io, appeler SharePoint, enlever les doublons, et retourner les articles en json
    return JSONResponse(content={"articles": []})


@app.get("/generate-newsletter")
async def generate_newsletter(service: Annotated[Service, Depends(get_service)]) -> Response:
    """Generate a newsletter from scraped news."""
    # TODO(jsleb333): Schedule this task to return immediately
    newsletter = await service.generate_newsletter()
    return Response(content=newsletter.to_markdown())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=str(config("DEVLOCAL_HOST", "localhost")),
        port=int(config("DEVLOCAL_PORT", 8000)),
        log_level="info",
    )
