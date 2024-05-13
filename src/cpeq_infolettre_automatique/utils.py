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
    try:
        data = [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]
    except json.JSONDecodeError as error:
        return {"error": "Failed to decode JSON", "details": str(error)}
    else:
        return data


def save_data_to_json(data: list[dict[str, str]], file_path: str = "output.json") -> str:
    """Saves processed data to a JSON file.

    Args:
        data (list[dict[str, str]]): Processed data to be saved.
        file_path (str): Path where the JSON data will be saved.

    Returns:
        str: A success message or an error message.
    """
    try:
        with Path.open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except OSError as error:
        return {"error": "Failed to write to file", "details": str(error)}
    else:
        return f"Data successfully saved to {file_path}"
