"""Utility functions for processing and saving data."""

import datetime as dt
from zoneinfo import ZoneInfo


def get_current_montreal_datetime() -> dt.datetime:
    """Get the current date and time in the Montreal timezone.

    Returns: The current date and time for Montreal.
    """
    timezone: ZoneInfo = ZoneInfo("America/Montreal")
    return dt.datetime.now(tz=timezone)
