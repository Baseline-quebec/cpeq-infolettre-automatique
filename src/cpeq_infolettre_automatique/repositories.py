"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
import datetime
import json
from abc import ABC, abstractmethod
from pathlib import Path

from O365.drive import File, Folder
from pydantic.json import pydantic_encoder
from pydantic_core import to_jsonable_python

from cpeq_infolettre_automatique.schemas import News, Newsletter, ScrapingProblem
from cpeq_infolettre_automatique.utils import (
    get_file_if_exists,
    get_or_create_subfolder,
)


class NewsRepository(ABC):
    """Abstract class for a News Repository."""

    @abstractmethod
    def setup(self) -> None:
        """Set up the repository."""

    @abstractmethod
    def create_news(self, news_list: News) -> None:
        """Save a single news."""

    @abstractmethod
    def create_many_news(self, news_list: list[News]) -> None:
        """Save all the news."""

    @abstractmethod
    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the newsletter."""

    @abstractmethod
    def create_scraping_problems(self, problems: list[ScrapingProblem]) -> None:
        """Save the Scraping Problems."""


class OneDriveNewsRepository(NewsRepository):
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

    _news_file_name = "news.csv"
    _newsletter_file_name = "newsletter.md"
    _scraping_problems_file_name = "scraping_problems.csv"

    def __init__(self, parent_folder: Folder) -> None:
        """Initializes the News repository.

        Args:
            news_folder: The O365 OneDrive Folder in which to store the News.
        """
        self.parent_folder = parent_folder

    def setup(self) -> None:
        """Initializes the Sharepoint subfolder in which to store this week's newsletter and news."""
        self.news_folder = get_or_create_subfolder(
            parent_folder=self.parent_folder,
            folder_name=str(datetime.datetime.now(tz=datetime.UTC).date()),
        )

    def create_news(self, news: News) -> None:
        """Adds a News to the repository, appending it to the CSV file if it exists, or creating the file of not.

        Args:
            news: The News to save.
        """
        self.create_many_news([news])

    def create_many_news(self, news_list: list[News]) -> None:
        """Save the list of News as a new CSV file in the OneDrive folder.

        Args:
            news_list: List of News to save.
        """
        file: File | None = get_file_if_exists(self.news_folder, self._news_file_name)
        if file is not None:
            file.download(name=self._news_file_name)

        with Path(self._news_file_name).open(mode="w", encoding="utf-8", newline="") as csvfile:
            csvwriter = csv.writer(
                csvfile,
                delimiter=",",
                quotechar="|",
                quoting=csv.QUOTE_MINIMAL,
                dialect="excel",
            )

            rows: list[list[str]] = []
            if file is None:
                # Add headers row if we are creating the file
                rows.append([keys.capitalize() for keys in News.model_fields])
            rows.extend([[str(value) for _, value in news] for news in news_list])

            csvwriter.writerows(rows)

        self.news_folder.upload_file(item=self._news_file_name)

    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
        Path(self._newsletter_file_name).write_text(newsletter.to_markdown(), encoding="utf-8")
        self.news_folder.upload_file(item=self._newsletter_file_name)

    def create_scraping_problems(self, problems: list[ScrapingProblem]) -> None:
        """Save the Scraping Problems in a CSV file.

        Args:
            problems: List of Scraping Problems to save.
        """
        file: File | None = get_file_if_exists(self.news_folder, self._scraping_problems_file_name)
        if file is not None:
            file.download(name=self._news_file_name)

        with Path(self._news_file_name).open(mode="w", encoding="utf-8", newline="") as csvfile:
            csvwriter = csv.writer(
                csvfile,
                delimiter=",",
                quotechar="|",
                quoting=csv.QUOTE_MINIMAL,
                dialect="excel",
            )

            rows: list[list[str]] = []
            if file is None:
                # Add headers row if we are creating the file
                rows.append([keys.capitalize() for keys in ScrapingProblem.model_fields])
            rows.extend([[str(value) for _, value in news] for news in problems])

            csvwriter.writerows(rows)

        self.news_folder.upload_file(item=self._news_file_name)


class LocalNewsRepository(NewsRepository):
    """Repository responsible for storing and retrieving News locally."""

    def __init__(self, path: Path) -> None:
        """Initializes the News repository."""
        self.path = path

    def setup(self) -> None:
        """Initializes the local folder in which to store the News."""
        self.path.mkdir(parents=True, exist_ok=True)

    def create_many_news(self, news_list: list[News]) -> None:
        """Save the list of News as a json file locally.

        Args:
            news_list: List of News to save.
        """
        file_name = "news.json"
        file_path = self.path / file_name
        json_news = [to_jsonable_python(news) for news in news_list]
        with file_path.open("w", encoding="UTF-8") as target:
            json.dump(
                json_news,
                target,
                ensure_ascii=False,
                indent=4,
                default=pydantic_encoder,
            )

    def create_news(self, news: News) -> None:
        """Save a single News as a json file locally.

        Args:
            news_list: List of News to save.
        """
        raise NotImplementedError

    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file locally.

        Args:
            newsletter: The Newsletter to save.
        """
        file_name = "newsletter.md"
        file_path = self.path / file_name
        file_path.write_text(newsletter.to_markdown(), encoding="utf-8")
