"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
from pathlib import Path
from typing import cast

from O365.drive import Drive, Folder

from cpeq_infolettre_automatique.schemas import News, Newsletter


class NewsRepository:
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

    def __init__(self, drive: Drive, folder_name: str) -> None:
        """Ctor."""
        self.drive = drive
        self.folder_name = folder_name

    def save_news(self, news_list: list[News]) -> None:
        """Save the list of News as a new CSV file in the OneDrive folder.

        Args:
            news_list: List of News to save.
        """
        file_path = f"{self.folder_name}/news.csv"
        Path(self.folder_name).mkdir(exist_ok=True)
        Path(file_path).touch(exist_ok=True)

        with Path(file_path).open(encoding="utf-8") as csvfile:
            csvwriter = csv.writer(
                csvfile, delimiter="|", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            rows: list[list[str]] = [["Title", "Content", "Date", "Rubric", "Summary"]]
            rows += [
                [
                    news.title,
                    news.content,
                    str(news.date),
                    str(news.rubric),
                    str(news.summary),
                ]
                for news in news_list
            ]
            csvwriter.writerows(rows)
            folder: Folder = cast(Folder, self.drive.get_root_folder())
            folder.upload_file(item=file_path)

    def save_newsletter(self, _: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
