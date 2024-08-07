"""Tests for utils module."""

import datetime as dt
from unittest.mock import patch

from cpeq_infolettre_automatique.utils import prepare_dates


def test_prepare_dates__when_default_args__returns_closest_monday_to_monday_period() -> None:
    """Test that the start and end dates are correctly prepared when no arguments are provided."""
    with patch(
        "cpeq_infolettre_automatique.utils.get_current_montreal_datetime"
    ) as get_current_datetime_mock:
        get_current_datetime_mock.return_value = dt.datetime(2024, 1, 9, tzinfo=dt.UTC)
        start_date, end_date = prepare_dates()
        first_monday = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        second_monday = dt.datetime(2024, 1, 8, tzinfo=dt.UTC)
        assert start_date == first_monday
        assert end_date == second_monday
