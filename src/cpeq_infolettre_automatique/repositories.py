"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
import datetime
import json
from abc import ABC, abstractmethod
from pathlib import Path

from O365.drive import Folder

from cpeq_infolettre_automatique.schemas import News, Newsletter
from cpeq_infolettre_automatique.utils import get_or_create_subfolder


class NewsRepository(ABC):
    """Abstract class for a News Repository."""

    @abstractmethod
    def setup(self) -> None:
        """Set up the repository."""

    @abstractmethod
    def create_news(self, news_list: list[News]) -> None:
        """Save all the news."""

    @abstractmethod
    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the newsletter."""


class OneDriveNewsRepository(NewsRepository):
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

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

    def create_news(self, news_list: list[News]) -> None:
        """Save the list of News as a new CSV file in the OneDrive folder.

        Args:
            news_list: List of News to save.
        """
        file_name = "news.csv"
        with Path(file_name).open(mode="w", encoding="utf-8", newline="") as csvfile:
            csvwriter = csv.writer(
                csvfile,
                delimiter=",",
                quotechar="|",
                quoting=csv.QUOTE_MINIMAL,
                dialect="excel",
            )
            rows: list[list[str]] = [
                [keys.capitalize() for keys in News.model_fields],
                *([str(value) for _, value in news] for news in news_list),
            ]

            csvwriter.writerows(rows)
            self.news_folder.upload_file(item=file_name)

    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
        file_name = "newsletter.md"
        Path(file_name).write_text(newsletter.to_markdown(), encoding="utf-8")
        self.news_folder.upload_file(item=file_name)


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
