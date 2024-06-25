"""cpeq-infolettre-automatique REST API."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import coloredlogs
import httpx
from decouple import config
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from cpeq_infolettre_automatique.config import sitemaps
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


webscraper_io_api_token = config("WEBSCRAPER_IO_API_KEY", default="")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle FastAPI startup and shutdown events."""
    # Startup events:
    # - Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    # Add coloredlogs' coloured StreamHandler to the root logger.
    # - Add coloredlogs' colored StreamHandler to the root logger.
    coloredlogs.install()

    app.state.http_client = httpx.AsyncClient()

    yield
    # Shutdown events.


app = FastAPI(lifespan=lifespan)


@app.get("/initiate_scraping")
async def initiate_scraping(request: Request) -> list[tuple[str, str]]:
    """Initiate web scraping jobs and process their data.

    Returns:
        list[tuple[str, str]]: A list of tuples associating a sitemap id to a job id
    """
    webscraper_client = WebScraperIoClient(
        http_client=request.app.state.http_client, api_token=webscraper_io_api_token
    )
    sitemap_ids = [sitemap["sitemap_id"] for sitemap in sitemaps]

    async def create_job(sitemap_id: str) -> tuple[str, str]:
        return (sitemap_id, await webscraper_client.create_scraping_job(sitemap_id))

    coroutines = [create_job(sitemap_id) for sitemap_id in sitemap_ids]
    return await asyncio.gather(*coroutines)


@app.get("/get-articles")
def get_articles_from_scraper() -> JSONResponse:
    """Retrieve and return articles.

    Returns:
        JSONResponse: An empty articles list response.
    """
    # Appeler l'API de webscraper.io, appeler SharePoint, enlever les doublons, et retourner les articles en json
    return JSONResponse(content={"articles": []})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=str(config("DEVLOCAL_HOST", "localhost")),
        port=int(config("DEVLOCAL_PORT", 8000)),
        log_level="info",
    )
