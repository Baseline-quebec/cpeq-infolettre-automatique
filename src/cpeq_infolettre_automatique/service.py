"""Service for the automatic newsletter generation that is called by the API."""

import asyncio
import datetime as dt
import logging
from collections.abc import AsyncIterator, Awaitable, Iterable

from cpeq_infolettre_automatique.config import Relevance
from cpeq_infolettre_automatique.news_classifier import NewsRelevancyClassifier
from cpeq_infolettre_automatique.news_producer import NewsProducer
from cpeq_infolettre_automatique.repositories import NewsRepository
from cpeq_infolettre_automatique.schemas import (
    News,
    Newsletter,
)
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


class Service:
    """Service for the automatic newsletter generation that is called by the API."""

    def __init__(
        self,
        start_date: dt.datetime,
        end_date: dt.datetime,
        webscraper_io_client: WebscraperIoClient,
        news_repository: NewsRepository,
        news_producer: NewsProducer,
        news_relevancy_classifier: NewsRelevancyClassifier,
    ) -> None:
        """Initialize the service with the repository and the generator."""
        self.start_date = start_date
        self.end_date = end_date
        self.webscraper_io_client = webscraper_io_client
        self.news_repository = news_repository
        self.news_producer = news_producer
        self.news_relevancy_classifier = news_relevancy_classifier

    async def generate_newsletter(
        self,
        *,
        delete_scraping_jobs: bool = True,
    ) -> Newsletter:
        """Generate the newsletter for the previous whole monday-to-sunday period. Summarization is done concurrently inside 'coroutines'.

        Returns:
            The formatted newsletter.
        """
        # For the moment, only the coroutine for scraped news is implemented.
        job_ids = await self.webscraper_io_client.get_scraping_jobs()
        logging.info("Nb Scraping jobs: %s", len(job_ids))
        scraped_news_coroutines = self._prepare_scraped_news_summarization_coroutines(
            self.start_date, self.end_date, job_ids
        )

        summarized_news = await asyncio.gather(*scraped_news_coroutines)
        flattened_news = [news for news_list in summarized_news for news in news_list]

        self.news_repository.create_many_news(flattened_news)
        if delete_scraping_jobs:
            await self.webscraper_io_client.delete_scraping_jobs()

        newsletter = Newsletter(
            news=flattened_news,
            news_datetime_range=(self.start_date, self.end_date),
            publication_datetime=self.end_date,
        )
        self.news_repository.create_newsletter(newsletter)
        return newsletter

    async def add_news(self, news: News) -> None:
        """Manually add a new News entry in the News repository."""
        if not self._news_in_date_range(news, self.start_date, self.end_date):
            msg = f"The News with title {news.title} was not published in the given time period."
            logging.warning(msg)
            return

        news = await self.news_producer.produce_news(news)
        self.news_repository.create_news(news)

    def _prepare_scraped_news_summarization_coroutines(
        self, start_date: dt.datetime, end_date: dt.datetime, job_ids: list[str]
    ) -> Iterable[Awaitable[Iterable[News]]]:
        """Prepare the summarization coroutines for concurrent summary generation of the news that are taken from the webscaper.

        Args:
            start_date: The start datetime of the newsletter.
            end_date: The end datetime of the newsletter.
            job_ids: The IDs of the scraping jobs.

        Returns:
            An iterable of summary generation coroutines to be run.
        """

        async def scraped_news_coroutine(job_id: str) -> list[News]:
            all_news = await self.webscraper_io_client.download_scraping_job_data(job_id)
            filtered_news = self._filter_all_news(
                all_news, start_date=start_date, end_date=end_date
            )
            coroutines = [self.news_producer.produce_news(news) async for news in filtered_news]
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
            if self._news_in_date_range(news, start_date, end_date):  # noqa: SIM102
                if await self._news_is_relevant(news):
                    yield news

    @staticmethod
    def _news_in_date_range(news: News, start_date: dt.datetime, end_date: dt.datetime) -> bool:
        """Check if the news is in the given date range.

        Args:
            news: The news data to check.
            start_date: The start datetime of the date range.
            end_date: The end datetime of the date range.

        Returns:
            True if the news is in the date range, False otherwise.
        """
        if news.datetime is None:
            msg = f"The News with title {news.title} has no date."
            logging.warning(msg)
            return False
        if not start_date <= news.datetime < end_date:
            msg = f"The News with title {news.title} was not published in the given time period."
            logging.warning(msg)
            return False
        return True

    async def _news_is_relevant(self, news: News) -> bool:
        """Check if the news is relevant.

        Args:
            news: The news data to check.

        Returns:
            True if the news is relevant, False otherwise.
        """
        relevance = await self.news_relevancy_classifier.predict(news)
        if relevance == Relevance.AUTRE:
            msg = f"The News with title {news.title} is not relevant."
            logging.warning(msg)
            return False
        return True
