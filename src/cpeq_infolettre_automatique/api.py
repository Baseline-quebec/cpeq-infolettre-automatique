"""cpeq-infolettre-automatique REST API."""

import logging

import coloredlogs
from decouple import config
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from cpeq_infolettre_automatique.config import sitemaps
from cpeq_infolettre_automatique.utils import process_raw_response, save_data_to_json
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


webscraper_io_api_token = config("WEBSCRAPER_IO_API_KEY", default="")

app = FastAPI()


@app.on_event("startup")
def startup_event() -> None:
    """Run API startup events with configured logging."""
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    # Add coloredlogs' coloured StreamHandler to the root logger.
    coloredlogs.install()


@app.get("/")
def read_root() -> str:
    """Read the API root endpoint.

    Returns:
        str: A simple "API is alive!" message.
    """
    return "API is alive!"


@app.get("/initiate_scraping")
def initiate_scraping() -> list[str]:
    """Initiate web scraping jobs and process their data.

    Returns:
        list[str]: A list of success messages or error messages for each job.
    """
    client = WebScraperIoClient(api_token=webscraper_io_api_token)
    sitemap_ids = [sitemap["sitemap_id"] for sitemap in sitemaps]
    job_ids = client.create_scraping_jobs(sitemap_ids)
    results = []
    for job_id in job_ids:
        raw_data = client.download_scraping_job_data(job_id)
        processed_data = process_raw_response(raw_data)
        if processed_data:
            save_message = save_data_to_json(processed_data, f"{job_id}_output.json")
            results.append(save_message)
        else:
            results.append(f"No data processed for job ID {job_id}")
    return results


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
        port=int(config("DEVLOCAL_PORT", 8001)),
    )
