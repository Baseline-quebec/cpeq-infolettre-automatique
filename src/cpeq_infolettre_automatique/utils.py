"""Utility functions for processing and saving data."""
import json
from typing import Any


def process_raw_response(raw_response: str) -> list[dict[str, Any]] | dict[str, str]:
    """Convert raw JSON lines into a list of dictionaries (valid JSON array) or return an error message.

    Args:
        raw_response (str): Raw response data in JSON lines format.

    Returns:
        list[dict[str, Any]] | dict[str, str]: List of dictionaries if successful, else an error message.
    """
    try:
        data = [json.loads(line) for line in raw_response.strip().split("\n") if line.strip()]
    except json.JSONDecodeError as error:
        return {"error": "Failed to decode JSON", "details": str(error)}
    else:
        return data


def save_data_to_json(data: list, file_path: str = "output.json") -> str:
    """Saves processed data to a JSON file.

    Args:
        data (list): Processed data to be saved.
        file_path (str): Path where the JSON data will be saved.

    Returns:
        str: A success message or an error message.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return f"Data successfully saved to {file_path}"
    except IOError as error:
        return {"error": "Failed to write to file", "details": str(error)}
