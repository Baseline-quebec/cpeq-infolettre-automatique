"""Service for the automatic newsletter generation that is called by the API."""

from datetime import datetime
from typing import Any

from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


# TODO: replace the following with actual type. Names are subject to change.  # noqa: TD002, TD003, FIX002
NewsRepository = Any
SummaryGenerator = Any
NewsLetterFormatter = Any
NewsLetter = Any


class Service:
    """Service for the automatic newsletter generation that is called by the API."""

    def __init__(
        self,
        webscraper_io_client: WebScraperIoClient,
        news_repository: NewsRepository,
        vectorstore: VectorStore,
        summary_generator: SummaryGenerator,
        newsletter_formatter: NewsLetterFormatter,
    ) -> None:
        """Initialize the service with the repository and the generator."""
        self.webscraper_io_client = webscraper_io_client
        self.repository = news_repository
        self.vectorstore = vectorstore
        self.generator = summary_generator
        self.formatter = newsletter_formatter

    def generate_newsletter(self, start_date: datetime, end_date: datetime) -> NewsLetter:
        """Generate the newsletter for the given date."""
        raw_news = self._get_news(start_date, end_date)
        news = self._process_news(raw_news)
        categorized_news = self._categorize_news(news)
        summaries = self._generate_summaries(categorized_news)
        newsletter = self._format_newsletter(summaries)
        return newsletter

    def _get_news(self, start_date: datetime, end_date: datetime) -> list[dict[str, Any]]:
        """Fetch news from the repository."""
        raise NotImplementedError

    def _process_news(self, raw_news: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process the raw news data."""
        raise NotImplementedError

    def _categorize_news(self, news: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Categorize the news data."""
        raise NotImplementedError

    def _generate_summaries(self, categorized_news: list[dict[str, Any]]) -> list[str]:
        """Generate summaries for the news data."""
        raise NotImplementedError

    def _format_newsletter(self, summaries: list[str]) -> NewsLetter:
        """Format the newsletter."""
        raise NotImplementedError
