"""Utility functions for processing and saving data."""

import datetime as dt
from typing import cast
from zoneinfo import ZoneInfo

from O365.drive import File, Folder


def get_current_montreal_datetime() -> dt.datetime:
    """Get the current date and time in the Montreal timezone.

    Returns: The current date and time for Montreal.
    """
    timezone: ZoneInfo = ZoneInfo("America/Montreal")
    return dt.datetime.now(tz=timezone)


def get_or_create_subfolder(parent_folder: Folder, folder_name: str) -> Folder:
    """Returns the subfolder with name $folder_name from the $parent_folder, creating it before if not found.

    Args:
        parent_folder: The parent folder.
        folder_name: The name of the subfolder.

    Returns: The subfolder with the name $folder_name.

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

    Returns: The file if found, None otherwise.
    """
    items = folder.get_items()
    filtered_items = tuple(filter(lambda item: item.name == file_name, items))
    if len(filtered_items) == 0:
        return None
    return filtered_items[0]
