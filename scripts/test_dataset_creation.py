"""The test dataset creation process."""

from pathlib import Path

from cpeq_infolettre_automatique.config import VectorstoreConfig
from cpeq_infolettre_automatique.dependencies import (
    HttpClientDependency,
    get_completion_model,
    get_embedding_model,
    get_news_producer,
    get_news_relevancy_classifier,
    get_news_rubric_classifier,
    get_openai_client,
    get_summary_generator,
    get_vectorstore_client,
    get_webscraperio_client,
)
from cpeq_infolettre_automatique.repositories import LocalNewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.vectorstore import Vectorstore


async def main() -> None:
    """Run the test dataset creation process."""
    HttpClientDependency.setup()
    http_client = HttpClientDependency()()
    webscraper_io_client = get_webscraperio_client(http_client)
    openai_client = get_openai_client()
    completion_model = get_completion_model(openai_client)
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        vectorstore = Vectorstore(
            vectorstore_client=vectorstore_client,
            embedding_model=embedding_model,
            vectorstore_config=VectorstoreConfig(collection_name="ClassificationEvaluation"),
        )
        summary_generator = get_summary_generator(completion_model, vectorstore)
        news_rubric_classifier = get_news_rubric_classifier(vectorstore)
        news_producer = get_news_producer(
            summary_generator=summary_generator,
            news_rubric_classifier=news_rubric_classifier,
        )
        news_relevancy_classifier = get_news_relevancy_classifier(vectorstore)
        local_news_repository = LocalNewsRepository(path=Path("data", "test"))
        service = Service(
            webscraper_io_client=webscraper_io_client,
            news_repository=local_news_repository,
            vectorstore=vectorstore,
            news_producer=news_producer,
            news_relevancy_classifier=news_relevancy_classifier,
        )

        await service.generate_newsletter(
            delete_scraping_jobs=False,
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
