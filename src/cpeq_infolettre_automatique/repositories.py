"""Repository responsible for storing and retrieving News from a OneDrive instance."""

import csv
import datetime
import io
from io import StringIO
from pathlib import Path

from O365.drive import File, Folder

from cpeq_infolettre_automatique.schemas import News, Newsletter
from cpeq_infolettre_automatique.utils import (
    get_file_if_exists,
    get_or_create_subfolder,
)


class NewsRepository:
    """Repository responsible for storing and retrieving News from a OneDrive instance."""

    _news_file_name = "news.csv"
    _newsletter_file_name = "newsletter.md"

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
        stream: StringIO = io.StringIO()

        file: File | None = get_file_if_exists(self.news_folder, self._news_file_name)
        if file is not None:
            file.download(output=stream)

        stream.seek(0, io.SEEK_END)  # Set position of stream at end to emulate append mode.

        csvwriter = csv.writer(
            csvfile=stream,
            delimiter="|",
            quotechar='"',
            dialect=csv.excel,
        )

        rows: list[list[str]] = []
        if file is None:
            # Add headers row if we are creating the file
            rows.append([keys.capitalize() for keys in News.model_fields])
        rows.append(*([str(value) for _, value in news] for news in news_list))

        csvwriter.writerows(rows)

        stream.seek(
            0, io.SEEK_END
        )  # Set position to end of stream to get stream size by calling tell()
        self.news_folder.upload_file(
            item=self._news_file_name,  # Required param, but will be ignored as we specify a stream to read from.
            stream=stream,
            stream_size=stream.tell(),
        )

    def create_newsletter(self, newsletter: Newsletter) -> None:
        """Save the Newsletter as a Markdown file in the OneDrive folder.

        Args:
            newsletter: The Newsletter to save.
        """
        Path(self._newsletter_file_name).write_text(newsletter.to_markdown(), encoding="utf-8")
        self.news_folder.upload_file(item=self._newsletter_file_name)
