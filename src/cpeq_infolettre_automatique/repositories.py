"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
from pathlib import Path

from O365.drive import Folder

from cpeq_infolettre_automatique.schemas import News, Newsletter


class NewsRepository:
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

    def __init__(self, news_folder: Folder) -> None:
        """Ctor."""
        self.news_folder = news_folder

    def save_news(self, news_list: list[News]) -> None:
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
            rows: list[list[str]] = [["Title", "Content", "Date", "Rubric", "Summary"]]
            rows += [
                [
                    news.title,
                    news.content,
                    str(news.datetime),
                    str(news.rubric),
                    str(news.summary),
                ]
                for news in news_list
            ]
            csvwriter.writerows(rows)
            self.news_folder.upload_file(item=file_name)

    def save_newsletter(self, _: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
