"""The test dataset creation process."""

import json
from pathlib import Path

from cpeq_infolettre_automatique.dependencies import (
    HttpClientDependency,
    get_completion_model,
    get_embedding_model,
    get_openai_client,
    get_reference_news_repository,
    get_summary_generator,
    get_vectorstore,
    get_vectorstore_client,
    get_webscraperio_client,
)
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import News, Newsletter
from cpeq_infolettre_automatique.service import Service


class LocalNewsRepository(NewsRepository):
    """Repository responsible for storing and retrieving News locally."""

    def __init__(self, path: Path) -> None:
        """Initializes the News repository."""
        self.path = path

    def setup(self) -> None:
        """Initializes the local folder in which to store the News."""
        self.path.mkdir(parents=True, exist_ok=True)

    def create_news(self, news_list: list[News]) -> None:
        """Save the list of News as a json file locally.

        Args:
            news_list: List of News to save.
        """
        file_name = "news.json"
        file_path = self.path / file_name
        with file_path.open("w", encoding="UTF-8") as target:
            json.dump(news_list, target, ensure_ascii=False, indent=4)

    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file locally.

        Args:
            newsletter: The Newsletter to save.
        """
        file_name = "newsletter.md"
        file_path = self.path / file_name
        file_path.write_text(newsletter.to_markdown(), encoding="utf-8")


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
        reference_news_repository = get_reference_news_repository(vectorstore_client)
        vectorstore = get_vectorstore(vectorstore_client, embedding_model)

        local_news_repository = LocalNewsRepository(path=Path("data", "test"))
        service = Service(
            webscraper_io_client=webscraper_io_client,
            news_repository=local_news_repository,
            reference_news_repository=reference_news_repository,
            vectorstore=vectorstore,
            summary_generator=summary_generator,
        )

        await service.generate_newsletter(delete_scraping_jobs=False)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
