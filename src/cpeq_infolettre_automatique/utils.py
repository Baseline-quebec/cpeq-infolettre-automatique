"""Utility functions for processing and saving data."""

import datetime as dt
from typing import cast
from zoneinfo import ZoneInfo

from O365.drive import Folder


def get_current_montreal_datetime() -> dt.datetime:
    """Get the current date and time in the Montreal timezone.

    Returns: The current date and time for Montreal.
    """
    timezone: ZoneInfo = ZoneInfo("America/Montreal")
    return dt.datetime.now(tz=timezone)


def get_or_create_subfolder(parent_folder: Folder, folder_name: str) -> Folder:
    """Returns the subfolder with name $folder_name from the $parent_folder, creating it before if not found."""
    folders = parent_folder.get_child_folders()
    filtered_folders = tuple(filter(lambda x: x.name == folder_name, folders))
    if len(filtered_folders) == 1:
        return cast(Folder, filtered_folders[0])
    if len(filtered_folders) == 0:
        return cast(Folder, parent_folder.create_child_folder(folder_name))
    msg = f"More than one folder with the name {folder_name} exist in the requested parent folder."
    raise RuntimeError(msg)
