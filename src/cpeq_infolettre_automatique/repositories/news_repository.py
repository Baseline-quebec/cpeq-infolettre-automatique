"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
import tempfile

from o365 import DriveItem

from cpeq_infolettre_automatique.schemas import News


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

        Note that a new file is created each time and will overwrite the previous one.

        Args:
            news_list: List of News to save.
        """
        with tempfile.NamedTemporaryFile(dir="", newline="") as csvfile:
            csvwriter = csv.writer(
                csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            csvwriter.writerows(["Title", "Content", "Date", "Rubric", "Summary"])

            for news in news_list:
                csvwriter.writerows([
                    news.title,
                    news.content,
                    str(news.date),
                    str(news.rubric),
                    str(news.summary),
                ])

            self.folder.upload_file()
