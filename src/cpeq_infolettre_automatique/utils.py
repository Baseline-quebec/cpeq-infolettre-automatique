"""Utility functions for processing and saving data."""

import json
from pathlib import Path


def save_data_to_json(data: list[dict[str, str]], file_path: str = "output.json") -> str:
    """Saves processed data to a JSON file.

    Args:
        data (list[dict[str, str]]): Processed data to be saved.
        file_path (str): Path where the JSON data will be saved.

    Returns:
        str: A success message or an error message.
    """
    with Path(file_path).open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    return f"Data successfully saved to {file_path}"
