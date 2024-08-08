"""cpeq-infolettre-automatique REST API."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

import coloredlogs
from decouple import config
from fastapi import BackgroundTasks, Depends, FastAPI
from fastapi.responses import Response

from cpeq_infolettre_automatique.dependencies import (
    HttpClientDependency,
    OneDriveDependency,
    VectorstoreClientDependency,
    get_service,
)
from cpeq_infolettre_automatique.schemas import AddNewsBody
from cpeq_infolettre_automatique.service import Service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
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
    VectorstoreClientDependency.setup()
    # TODO(Olivier Belhumeur): Add News Classifier setup here when deploying to production.

    yield

    # Shutdown events.
    await HttpClientDependency.teardown()
    VectorstoreClientDependency.teardown()


app = FastAPI(lifespan=lifespan)


@app.get("/generate-newsletter")
def generate_newsletter(
    service: Annotated[Service, Depends(get_service)],
    folder_name: Annotated[str, Depends(OneDriveDependency.get_folder_name)],
    background_tasks: BackgroundTasks,
) -> Response:
    """Generate a newsletter from scraped news.

    Returns:
        A message indicating where the generated Newsletter will be saved.

    Note:
        This task is scheduled to return the news from last week's Monday to last week's Sunday.

        It might take a while to complete.
    """
    background_tasks.add_task(
        service.generate_newsletter,
        delete_scraping_jobs=False,
    )
    return Response(
        content=f"Génération de l'infolettre en cours. Celle-ci sera sauvegardée sous peu sur Sharepoint dans le dossier {folder_name}."
    )


@app.post("/add-news")
async def add_news(body: AddNewsBody, service: Annotated[Service, Depends(get_service)]) -> None:
    """Endpoint to manually add a news to this week's newsletter."""
    await service.add_news(body.to_news())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=str(config("DEVLOCAL_HOST", "localhost")),
        port=int(config("DEVLOCAL_PORT", 8000)),
        log_level="trace",
    )
