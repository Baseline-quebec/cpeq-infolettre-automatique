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
        """Generate the newsletter for the date range specified at Service initialization. Summarization is done concurrently inside 'coroutines'.

        The steps are:
            1. Get stored news from OneDrive
            2. Get scraped news from Webscraper.io that are not in the stored news
            3. Filter out irrelevant news from scraped news
            4. Summarize all news without summaries
            5. Store the summarized news in the OneDrive
            6. Generate the newsletter

        Stored news and scraped news are processed differently in order to process them concurrently.

        Args:
            delete_scraping_jobs: Whether to delete the scraping jobs after processing

        Returns:
            The formatted newsletter.
        """
        stored_news = self.news_repository.get_all_news()
        already_scraped_jobs = {news.job_id for news in stored_news}

        scraping_job_ids = await self.webscraper_io_client.get_scraping_jobs()
        unscraped_job_ids = [
            job_id for job_id in scraping_job_ids if job_id not in already_scraped_jobs
        ]
        logging.info(
            "Number of scraping jobs to process: %s (%s was already done)",
            len(unscraped_job_ids),
            len(already_scraped_jobs),
        )

        scraped_news_coroutines = self._prepare_scraped_news_summarization_coroutines(
            self.start_date, self.end_date, unscraped_job_ids
        )

        summarized_news = await asyncio.gather(*scraped_news_coroutines)
        all_news = [news for news_list in summarized_news for news in news_list] + stored_news

        self.news_repository.create_many_news(all_news)

        if delete_scraping_jobs:
            await self.webscraper_io_client.delete_scraping_jobs()

        newsletter = Newsletter(
            news=all_news,
            news_datetime_range=(self.start_date, self.end_date),
            publication_datetime=self.end_date,
        )
        self.news_repository.create_newsletter(newsletter)

        return newsletter

    async def add_news(self, news: News) -> None:
        """Manually add a new News entry in the News repository."""
        if not self._news_in_date_range(news, self.start_date, self.end_date):
            # The user could want to exceptionally add an old news to the newsletter. Just log a warning.
            msg = f"The News with title {news.title} was not published in the given time period."
            logging.warning(msg)

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
