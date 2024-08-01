"""File implementing the WebscraperIO Cron sitemaps."""

import enum
import logging

import httpx
from decouple import config

from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


class Weekday(enum.Enum):
    """An enumeration of the days of the week."""

    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebScraperIOCronScheduler(WebscraperIoClient):
    """A class to schedule sitemaps using the WebScraper.io API."""

    def __init__(self, http_client: httpx.AsyncClient, api_token: str) -> None:
        """Initialize the WebScraperCronScheduler with the provided API token.

        Args:
            http_client (httpx.AsyncClient): The AsyncClient used for API calls.
            api_token (str): The API token used for authentication.
        """
        super().__init__(http_client, api_token)

    async def schedule_sitemap(self, sitemap_id: str, weekday: Weekday) -> None:
        """Schedules a sitemap for scraping on a specific weekday.

        Note:
            https://webscraper.io/documentation/web-scraper-cloud/api#:~:text=Enable%20Sitemap%20Scheduler
        Args:
            sitemap_id: ID of the sitemap to schedule.
            weekday: The weekday to schedule the sitemap on.
        """
        url: str = f"{self._base_url}/sitemap/{sitemap_id}/enable-scheduler"
        data: dict[str, str | int] = {
            "cron_minute": 0,
            "cron_hour": 0,
            "cron_day": "*",
            "cron_month": "*",
            "cron_weekday": weekday.value,
            "page_load_delay": 3000,
            "request_interval": 3000,
            "cron_timezone": "America/Toronto",
            "driver": "fulljs",
            "proxy": 0,
        }
        response: httpx.Response = await self._client.post(
            url,
            json=data,
            headers=self._headers,
            params={"api_token": self._api_token},
        )
        response.raise_for_status()

    async def schedule_sitemaps(self, weekday: Weekday) -> None:
        """Schedules all sitemaps for scraping on a specific weekday.

        Args:
            weekday: The weekday to schedule the sitemaps on.
        """
        sitemaps = await self.get_sitemaps()
        for sitemap in sitemaps:
            await self.schedule_sitemap(sitemap["id"], weekday)


async def main(weekday: Weekday) -> None:
    """Schedule all sitemaps for scraping on a specific weekday."""
    async with httpx.AsyncClient() as client:
        webscraper_io_scheduler = WebScraperIOCronScheduler(
            client, api_token=config("WEBSCRAPER_IO_API_KEY")
        )
        await webscraper_io_scheduler.schedule_sitemaps(weekday)


if __name__ == "__main__":
    import asyncio

    weekday = Weekday.MONDAY
    asyncio.run(main(weekday))
