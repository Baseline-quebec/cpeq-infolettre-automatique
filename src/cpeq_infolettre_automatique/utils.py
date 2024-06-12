"""Utility functions for processing and saving data."""

import json
from pathlib import Path


def process_raw_response(raw_response: str) -> list[dict[str, str]]:
    """Converts raw JSON lines into a list of dictionaries (valid JSON array).

    Args:
        raw_response (str): The raw JSON lines to be processed.

    Returns:
        list[dict[str, str]]: A list of dictionaries or a list with an error message.
    """
    return [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]


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
