"""Service for the automatic newsletter generation that is called by the API."""

import asyncio
from collections.abc import Awaitable
from datetime import datetime
from typing import Any

from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import VectorStore
from cpeq_infolettre_automatique.webscraper_io_client import WebScraperIoClient


# TODO: replace the following with actual type. Names are subject to change.  # noqa: TD002
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

    async def generate_newsletter(
        self, start_date: datetime, end_date: datetime
    ) -> Awaitable[NewsLetter]:
        """Generate the newsletter for the given date concurrently. Summarization is done concurrently inside 'pipelines'.

        Args:
            start_date: The start date of the newsletter.
            end_date: The end date of the newsletter.

        Returns: The formatted newsletter as an awaitable object.
        """
        pipelines = await self._prepare_summarization_pipelines(start_date, end_date)
        summarized_news = await asyncio.gather(*pipelines)
        flatten_news = [news for news_list in summarized_news for news in news_list]
        newsletter = self._format_newsletter(flatten_news)
        return newsletter

    async def _prepare_summarization_pipelines(
        self, start_date: datetime, end_date: datetime
    ) -> list[Awaitable[list[News]]]:
        """Prepare the async pipelines for concurrent summary generation of the news.

        For the moment, only the pipeline for scraped news is implemented.

        Args:
            start_date: The start date of the newsletter.
            end_date: The end date of the newsletter.

        Returns: A list of summary generation pipelines to be run.
        """
        job_ids = await self.webscraper_io_client.get_scraping_jobs(start_date, end_date)

        async def scraped_news_pipeline(job_id: str) -> list[News]:
            all_news = await self.webscraper_io_client.get_scraping_job_data(job_id)
            filtered_news = self._filter_news(all_news, start_date=start_date, end_date=end_date)
            summarized_news = await asyncio.gather(*[
                self._summarize_news(news) for news in filtered_news
            ])
            return summarized_news

        pipelines: list[Awaitable[list[News]]] = [
            scraped_news_pipeline(job_id) for job_id in job_ids
        ]

        # Add more pipelines here for other sources of news data.

        return pipelines

    def _filter_news(
        self, all_news: list[News], start_date: datetime, end_date: datetime
    ) -> list[News]:
        """Preprocess the raw news by keeping only news published within start_date and end_date and are relevant.

        Args:
            all_news: The raw news data.
            start_date: The start date of the newsletter.
            end_date: The end date of the newsletter.

        Returns: The filtered news data.
        """
        filtered_news = []
        for news in all_news:
            if news.date is None:
                continue  # TODO(JSL): In future version, check if news exists in the repository.
            if not start_date <= news.date <= end_date:
                continue
            news.rubric = self.vectorstore.classify_rubric(news)
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
        examples = await self.vectorstore.get_examples(news)
        news.summary = await self.generator.generate_summary(news, examples)
        return news

    async def _format_newsletter(self, news: list[News]) -> NewsLetter:
        """Format the news into a newsletter."""
        raise NotImplementedError
