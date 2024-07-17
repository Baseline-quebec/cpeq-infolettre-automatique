"""The test dataset creation process."""

from pathlib import Path

from cpeq_infolettre_automatique.dependencies import (
    HttpClientDependency,
    get_completion_model,
    get_embedding_model,
    get_news_classifier,
    get_openai_client,
    get_summary_generator,
    get_vectorstore,
    get_vectorstore_client,
    get_webscraperio_client,
)
from cpeq_infolettre_automatique.repositories import LocalNewsRepository
from cpeq_infolettre_automatique.service import Service


async def main() -> None:
    """Run the test dataset creation process."""
    HttpClientDependency.setup()
    http_client = HttpClientDependency()()
    webscraper_io_client = get_webscraperio_client(http_client)
    openai_client = get_openai_client()
    completion_model = get_completion_model(openai_client)
    summary_generator = get_summary_generator(completion_model)
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        vectorstore = get_vectorstore(vectorstore_client, embedding_model)
        news_classifier = get_news_classifier(vectorstore)
        local_news_repository = LocalNewsRepository(path=Path("data", "test"))
        service = Service(
            webscraper_io_client=webscraper_io_client,
            news_repository=local_news_repository,
            news_classifier=news_classifier,
            vectorstore=vectorstore,
            summary_generator=summary_generator,
        )

        await service.generate_newsletter(delete_scraping_jobs=False)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
