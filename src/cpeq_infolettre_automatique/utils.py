"""Utility functions for processing and saving data."""

import datetime as dt
from typing import cast
from zoneinfo import ZoneInfo

from O365.drive import File, Folder


def prepare_dates(
    start_date: dt.datetime | None = None,
    end_date: dt.datetime | None = None,
) -> tuple[dt.datetime, dt.datetime]:
    """Prepare the start and end dates for the newsletter.

    Notes:
        If no dates are provided, the newsletter will be generated for the previous whole monday-to-sunday period.

    Args:
        start_date: The start datetime of the newsletter.
        end_date: The end datetime of the newsletter.

    Returns:
        The start and end dates for the newsletter.
    """
    if end_date is None:
        current_date = get_current_montreal_datetime().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = current_date - dt.timedelta(days=current_date.weekday())
    if start_date is None:
        start_date = end_date - dt.timedelta(days=7)
    return start_date, end_date


def get_current_montreal_datetime() -> dt.datetime:
    """Get the current date and time in the Montreal timezone.

    Returns:
        The current date and time for Montreal.
    """
    timezone: ZoneInfo = ZoneInfo("America/Montreal")
    return dt.datetime.now(tz=timezone)


def get_or_create_subfolder(parent_folder: Folder, folder_name: str) -> Folder:
    """Returns the subfolder with name $folder_name from the $parent_folder, creating it before if not found.

    Args:
        parent_folder: The parent folder.
        folder_name: The name of the subfolder.

    Returns:
        The subfolder with the name $folder_name.

    Raises:
        RuntimeError: If more than one folder with the name $folder_name exist in the requested parent folder.
    """
    folders = parent_folder.get_child_folders()
    filtered_folders = tuple(filter(lambda x: x.name == folder_name, folders))
    if len(filtered_folders) == 1:
        return cast(Folder, filtered_folders[0])
    if len(filtered_folders) == 0:
        return cast(Folder, parent_folder.create_child_folder(folder_name))
    msg = f"More than one folder with the name {folder_name} exist in the requested parent folder."
    raise RuntimeError(msg)


def get_file_if_exists(folder: Folder, file_name: str) -> File | None:
    """Gets the specified file from the specified folder. Returns None if no such file exists in the folder.

    Args:
        folder: The folder to search for the file.
        file_name: The name of the file to search for.

    Returns:
        The file if found, None otherwise.
    """
    items = folder.get_items()
    filtered_items = tuple(filter(lambda item: item.name == file_name, items))
    if len(filtered_items) == 0:
        return None
    return filtered_items[0]
