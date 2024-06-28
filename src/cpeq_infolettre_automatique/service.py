"""Service for the automatic newsletter generation that is called by the API."""

import asyncio
import datetime
from collections.abc import Awaitable, Iterable
from typing import Any
from zoneinfo import ZoneInfo

from cpeq_infolettre_automatique.reference_news_repository import ReferenceNewsRepository
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


# TODO: replace the following with actual type. Names are subject to change.  # noqa: TD002
SummaryGenerator = Any
NewsletterFormatter = Any
Newsletter = Any
NewsletterRepository = Any
NewsRepository = Any


class Service:
    """Service for the automatic newsletter generation that is called by the API."""

    def __init__(
        self,
        webscraper_io_client: WebScraperIoClient,
        news_repository: NewsRepository,
        reference_news_repository: ReferenceNewsRepository,
        newsletter_repository: NewsletterRepository,
        vectorstore: VectorStore,
        summary_generator: SummaryGenerator,
        newsletter_formatter: NewsletterFormatter,
    ) -> None:
        """Initialize the service with the repository and the generator."""
        self.webscraper_io_client = webscraper_io_client
        self.reference_news_repository = reference_news_repository
        self.news_repository = news_repository
        self.newsletter_repository = newsletter_repository
        self.vectorstore = vectorstore
        self.summary_generator = summary_generator
        self.formatter = newsletter_formatter

    async def generate_newsletter(self) -> Newsletter:
        """Generate the newsletter for the previous whole monday-to-sunday period. Summarization is done concurrently inside 'coroutines'.

        Returns: The formatted newsletter.
        """
        start_date, end_date = self._prepare_dates()

        # For the moment, only the coroutine for scraped news is implemented.
        job_ids = await self.webscraper_io_client.get_scraping_jobs()
        scraped_news_coroutines = self._prepare_scraped_news_summarization_coroutines(
            start_date, end_date, job_ids
        )

        summarized_news = await asyncio.gather(*scraped_news_coroutines)
        flattened_news = [news for news_list in summarized_news for news in news_list]
        await self.news_repository.create(flattened_news)
        await self.webscraper_io_client.delete_scraping_jobs()
        newsletter = self._format_newsletter(flattened_news)
        await self.newsletter_repository.create(newsletter)
        return newsletter

    @staticmethod
    def _get_current_datetime() -> datetime.datetime:
        """Get the current date and time in the Montreal timezone.

        Returns: The current date and time.
        """
        return datetime.datetime.now(ZoneInfo("America/Montreal"))

    @classmethod
    def _prepare_dates(
        cls,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
    ) -> tuple[datetime.datetime, datetime.datetime]:
        """Prepare the start and end dates for the newsletter.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.

        Returns: The start and end dates for the newsletter.
        """
        if end_date is None:
            current_date = cls._get_current_datetime()
            end_date = current_date - datetime.timedelta(days=current_date.weekday())
        if start_date is None:
            start_date = end_date - datetime.timedelta(days=7)
        return start_date, end_date

    def _prepare_scraped_news_summarization_coroutines(
        self, start_date: datetime.datetime, end_date: datetime.datetime, job_ids: list[str]
    ) -> Iterable[Awaitable[Iterable[News]]]:
        """Prepare the summarization coroutines for concurrent summary generation of the news that are taken from the webscaper.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.
            job_ids: The IDs of the scraping jobs.

        Returns: An iterable of summary generation coroutines to be run.
        """

        async def scraped_news_coroutine(job_id: str) -> list[News]:
            all_news = await self.webscraper_io_client.get_scraping_job_data(job_id)
            filtered_news = await self._filter_news(
                all_news, start_date=start_date, end_date=end_date
            )
            summarized_news = await asyncio.gather(
                *(self._summarize_news(news) for news in filtered_news)
            )
            return summarized_news

        return (scraped_news_coroutine(job_id) for job_id in job_ids)

    async def _filter_news(
        self, all_news: list[News], start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list[News]:
        """Preprocess the raw news by keeping only news published within start_date and end_date and are relevant.

        Args:
            all_news: The raw news data.
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.

        Returns: The filtered news data.
        """
        filtered_news = []
        for news in all_news:
            if news.datetime is None:
                continue
            if not start_date <= news.datetime < end_date:
                continue
            news.rubric = await self.vectorstore.classify_news_rubric(news)
            if news.rubric is None:
                continue
            filtered_news.append(news)

        return filtered_news

    async def _summarize_news(self, news: News) -> News:
        """Generate summaries for the news data.

        Args:
            news: The news data to summarize.

        Returns: The news data with the summary.
        """
        if news.rubric is None:
            error_msg = "Rubric must be set before summarization"
            raise ValueError(error_msg)
        examples = self.reference_news_repository.read_many_by_rubric(news.rubric, nb_per_page=5)
        news.summary = await self.summary_generator.generate_summary(news, examples)
        return news

    def _format_newsletter(self, news: list[News]) -> Newsletter:
        """Format the news into a newsletter."""
        raise NotImplementedError
