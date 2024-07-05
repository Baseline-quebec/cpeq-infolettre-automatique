"""Service for the automatic newsletter generation that is called by the API."""

import asyncio
import datetime as dt
from collections.abc import AsyncIterator, Awaitable, Iterable
from typing import Any

from cpeq_infolettre_automatique.reference_news_repository import (
    ReferenceNewsRepository,
)
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import (
    News,
    Newsletter,
)
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


# TODO: replace the following with actual type. Names are subject to change.  # noqa: TD002
SummaryGenerator = Any
NewsletterFormatter = Any


class Service:
    """Service for the automatic newsletter generation that is called by the API."""

    def __init__(
        self,
        webscraper_io_client: WebscraperIoClient,
        news_repository: NewsRepository,
        reference_news_repository: ReferenceNewsRepository,
        vectorstore: Vectorstore,
        summary_generator: SummaryGenerator,
        newsletter_formatter: NewsletterFormatter,
    ) -> None:
        """Initialize the service with the repository and the generator."""
        self.webscraper_io_client = webscraper_io_client
        self.reference_news_repository = reference_news_repository
        self.news_repository = news_repository
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
        self.news_repository.create_news(flattened_news)
        await self.webscraper_io_client.delete_scraping_jobs()
        newsletter = self._format_newsletter(flattened_news)
        self.news_repository.create_newsletter(newsletter)
        return newsletter

    @staticmethod
    def _prepare_dates(
        start_date: dt.datetime | None = None,
        end_date: dt.datetime | None = None,
    ) -> tuple[dt.datetime, dt.datetime]:
        """Prepare the start and end dates for the newsletter.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.

        Returns: The start and end dates for the newsletter.
        """
        if end_date is None:
            current_date = get_current_montreal_datetime()
            end_date = current_date - dt.timedelta(days=current_date.weekday())
        if start_date is None:
            start_date = end_date - dt.timedelta(days=7)
        return start_date, end_date

    def _prepare_scraped_news_summarization_coroutines(
        self, start_date: dt.datetime, end_date: dt.datetime, job_ids: list[str]
    ) -> Iterable[Awaitable[Iterable[News]]]:
        """Prepare the summarization coroutines for concurrent summary generation of the news that are taken from the webscaper.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.
            job_ids: The IDs of the scraping jobs.

        Returns: An iterable of summary generation coroutines to be run.
        """

        async def scraped_news_coroutine(job_id: str) -> list[News]:
            all_news = await self.webscraper_io_client.download_scraping_job_data(job_id)
            filtered_news = self._filter_news(all_news, start_date=start_date, end_date=end_date)
            coroutines = [self._summarize_news(news) async for news in filtered_news]
            summarized_news = await asyncio.gather(*coroutines)
            return summarized_news

        return (scraped_news_coroutine(job_id) for job_id in job_ids)

    async def _filter_news(
        self, all_news: Iterable[News], start_date: dt.datetime, end_date: dt.datetime
    ) -> AsyncIterator[News]:
        """Preprocess the raw news by keeping only news published within start_date and end_date and are relevant.

        Args:
            all_news: The raw news data.
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.

        Returns: The filtered news data.
        """
        for news in all_news:
            if news.datetime is None:
                continue
            if not start_date <= news.datetime < end_date:
                continue
            rubric_classification = await self.vectorstore.classify_news_rubric(news)
            if rubric_classification is not None:
                news.rubric = rubric_classification
            yield news

    async def _summarize_news(self, news: News) -> News:
        """Generate summaries for the news data.

        Args:
            classified_news: The classified news data to summarize.

        Returns: The news data with the summary.
        """
        if news.rubric is None:
            raise ValueError

        examples = self.reference_news_repository.read_many_by_rubric(news.rubric, nb_per_page=5)
        news.summary = await self.summary_generator.generate_summary(news, examples)
        return news

    def _format_newsletter(self, _: list[News]) -> Newsletter:
        """Format the news into a newsletter."""
        raise NotImplementedError
