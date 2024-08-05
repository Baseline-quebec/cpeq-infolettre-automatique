"""Service for the automatic newsletter generation that is called by the API."""

import asyncio
import datetime as dt
from collections.abc import AsyncIterator, Awaitable, Iterable

from cpeq_infolettre_automatique.reference_news_repository import (
    ReferenceNewsRepository,
)
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import (
    News,
    Newsletter,
)
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


class Service:
    """Service for the automatic newsletter generation that is called by the API."""

    def __init__(
        self,
        webscraper_io_client: WebscraperIoClient,
        news_repository: NewsRepository,
        reference_news_repository: ReferenceNewsRepository,
        vectorstore: Vectorstore,
        summary_generator: SummaryGenerator,
    ) -> None:
        """Initialize the service with the repository and the generator."""
        self.webscraper_io_client = webscraper_io_client
        self.reference_news_repository = reference_news_repository
        self.news_repository = news_repository
        self.vectorstore = vectorstore
        self.summary_generator = summary_generator

    async def generate_newsletter(self, *, delete_scraping_jobs: bool = True) -> str:
        """Generate the newsletter for the previous whole monday-to-sunday period. Summarization is done concurrently inside 'coroutines'.

        Returns: The formatted newsletter.
        """
        start_date, end_date = self._prepare_dates()
        self.news_repository.setup(str(end_date.date()))

        # For the moment, only the coroutine for scraped news is implemented.
        job_ids = await self.webscraper_io_client.get_scraping_jobs()
        scraped_news_coroutines = self._prepare_scraped_news_summarization_coroutines(
            start_date, end_date, job_ids
        )

        summarized_news = await asyncio.gather(*scraped_news_coroutines)
        flattened_news = [news for news_list in summarized_news for news in news_list]
        self.news_repository.create_many_news(flattened_news)
        if delete_scraping_jobs:
            await self.webscraper_io_client.delete_scraping_jobs()

        newsletter = Newsletter(
            news=flattened_news,
            news_datetime_range=(start_date, end_date),
            publication_datetime=end_date,
        )
        self.news_repository.create_newsletter(newsletter)
        return f"{self.news_repository.parent_folder.name}/{self.news_repository.news_folder.name}"

    async def add_news(self, news: News) -> None:
        """Manually add a new News entry in the News repository."""
        start_date, end_date = self._prepare_dates()
        self.news_repository.setup(str(end_date.date()))
        await self._filter_news(news, start_date, end_date)
        await self._summarize_news(news)
        self.news_repository.create_news(news)

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
            filtered_news = self._filter_all_news(
                all_news, start_date=start_date, end_date=end_date
            )
            coroutines = [self._summarize_news(news) async for news in filtered_news]
            summarized_news = await asyncio.gather(*coroutines)
            return summarized_news

        return (scraped_news_coroutine(job_id) for job_id in job_ids)

    async def _filter_all_news(
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
            try:
                yield await self._filter_news(news, start_date, end_date)
            except ValueError:
                continue

    async def _filter_news(
        self, news: News, start_date: dt.datetime, end_date: dt.datetime
    ) -> News:
        if news.datetime is None:
            msg = f"The News with title {news.title} has no date."
            raise ValueError(msg)
        if not start_date <= news.datetime < end_date:
            msg = f"The News with title {news.title} was not published in the given time period."
            raise ValueError(msg)
        rubric_classification = await self.vectorstore.classify_news_rubric(news)
        if rubric_classification is not None:
            news.rubric = rubric_classification
        return news

    async def _summarize_news(self, classified_news: News) -> News:
        """Generate summaries for the news data.

        Args:
            classified_news: The classified news data to summarize.

        Returns: The news data with the summary.
        """
        if classified_news.rubric is None:
            error_msg = "The news must be classified before summarization"
            raise ValueError(error_msg)

        examples = self.reference_news_repository.read_many_by_rubric(classified_news.rubric)
        classified_news.summary = await self.summary_generator.generate(classified_news, examples)
        return classified_news

    @staticmethod
    def _prepare_dates(
        start_date: dt.datetime | None = None,
        end_date: dt.datetime | None = None,
    ) -> tuple[dt.datetime, dt.datetime]:
        """Prepare the start and end dates for the newsletter.

        Notes:
            If no dates are provided, the newsletter will be generated for the previous whole monday-to-sunday period.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.

        Returns: The start and end dates for the newsletter.
        """
        if end_date is None:
            current_date = get_current_montreal_datetime().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_date = current_date - dt.timedelta(days=current_date.weekday())
        if start_date is None:
            start_date = end_date - dt.timedelta(days=7)
        return start_date, end_date
