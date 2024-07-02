"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
import tempfile
from pathlib import Path

from o365 import DriveItem

from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.service import Newsletter


# https://github.com/O365/python-o365?tab=readme-ov-file#onedrive
class NewsRepository:
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

    def __init__(self, folder: DriveItem) -> None:
        """Ctor."""
        self.folder = folder

    # https://docs.python.org/3/library/tempfile.html#examples
    # https://docs.python.org/3/library/csv.html
    def save_news(self, news_list: list[News]) -> None:
        """Save the list of News as a new CSV file in the OneDrive folder.

        Args:
            news_list: List of News to save.
        """
        with (
            tempfile.NamedTemporaryFile(prefix="news-", suffix=".csv", newline="") as tmpfile,
            Path(tmpfile.name).open(encoding="utf-8") as csvfile,
        ):
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
            self.folder.upload_file(tmpfile.name)

    def save_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
