"""Client module for openAI API interaction."""

import json
import logging
from pathlib import Path

import numpy as np
import openai
import tiktoken
from config import EMBEDDING_MODEL, MAX_TOKENS, TOKEN_ENCODING
from openai import OpenAI


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VectorStore:
    """Handles vector storage and retrieval using embeddings."""
    def __init__(self, client: OpenAI, filepath: str) -> None:
        """Initialize the VectorStore with the provided OpenAI client and embedded data.

        Args:
            client (OpenAI): An instance of the OpenAI client to handle API calls.
            filepath (str): The path to the JSON file containing embedded data.
        """
        self.client = client
        self.data = self.load_embedded_data(filepath)
        if self.data:
            self.global_mean_embedding = self.calculate_global_mean_embedding()

    def _load_embedded_data(self, filepath: str) -> dict | None:
        """Load embedded data from a JSON file.

        Args:
            filepath (str): The path to the JSON file.

        Returns:
            Union[dict, None]: The data loaded from the JSON file, or None if an error occurs.
        """
        try:
            with Path.open(filepath) as file:
                return json.load(file)
        except Exception:
            logger.exception("Error loading embedded data from %s", filepath)
            return None

    def _calculate_global_mean_embedding(self) -> np.ndarray:
        """Calculate the global mean embedding from all embeddings in the dataset.

        Returns:
            np.ndarray: A numpy array representing the global mean embedding.
        """
        embeddings = [
            np.array(ex["embedding"]) for section in self.data for ex in section["examples"]
        ]
        return np.mean(embeddings, axis=0) if embeddings else np.zeros_like(embeddings[0])

    def get_category_embeddings(
        self, exclude_rubric: str = None, exclude_title: str = None
    ) -> dict[str, np.ndarray]:
        """Retrieve embeddings for each category, optionally excluding a specific example, and adjust by the global mean embedding.

        Args:
            exclude_rubric (str, optional): The rubric of the example to exclude.
            exclude_title (str, optional): The title of the example to exclude.

        Returns:
            dict[str, np.ndarray]: A dictionary of category names to their mean adjusted embeddings.
        """
        category_embeddings = {}
        for section in self.data:
            embeddings = [
                np.array(ex["embedding"]) - self.global_mean_embedding
                for ex in section["examples"]
                if not (section["rubric"] == exclude_rubric and ex["title"] == exclude_title)
            ]
            if embeddings:
                category_embeddings[section["rubric"]] = np.mean(embeddings, axis=0)
        return category_embeddings

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculates the cosine similarity between two vectors.

        Args:
            vec1 (np.array): The first vector.
            vec2 (np.array): The second vector.

        Returns:
            float: The cosine similarity score, between -1 (opposite) and 1 (identical).
        """
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    def get_average_embeddings(
        self, rubrics_data: list[dict[str, str | list[dict[str, str]]]], model: str = EMBEDDING_MODEL,
    ) -> dict[str, list[float]]:
        """Calculates average embeddings for each rubric using provided examples.

        Args:
            model (str): The OpenAI model to use for generating embeddings.
            rubrics_data (list[dict[str, str | list[dict[str, str]]]]): A list of rubric sections, each containing examples.

        Returns:
            dict[str, list[float]]: A dictionary mapping rubric names to their average embedding vectors.
        """
        rubric_embeddings = {}

        for rubric_section in rubrics_data:
            rubric_name = rubric_section["rubric"]
            articles = rubric_section["examples"]
            all_embeddings = []

            for article in articles:
                input_text = f"{article["title"]} {article["summary"]}"  # Combine title and summary for embedding
                try:
                    response = openai.embeddings.create(input=input_text, model=model)
                    embedding_vector = response.data[0].embedding
                    all_embeddings.append(embedding_vector)
                    logger.info(
                        "Embedding retrieved for: %s (Vector length: %d)",
                        article["title"],
                        len(embedding_vector)
                    )
                except Exception as e:
                    logger.warning(f"Failed to retrieve embeddings for {article['title']}: {e!s}")

            # Calculate the average embedding if any embeddings were successfully retrieved
            if all_embeddings:
                average_embedding = np.mean(all_embeddings, axis=0)
                rubric_embeddings[rubric_name] = (
                    average_embedding.tolist()
                )  # Convert numpy array to list for JSON compatibility
                logger.info(f"Average embedding calculated for rubric: {rubric_name}")

        return rubric_embeddings

    # Function to get trunkated embedding
    @staticmethod
    def encode_with_truncation(text: str, max_tokens: int = MAX_TOKENS) -> tuple[str, int]:
        """Encode text into tokens using a specified model's tokenizer, truncating to a maximum number of tokens if necessary.

        Args:
            text (str): The text to be tokenized and truncated.
            max_tokens (int): The maximum number of tokens allowed.

        Returns:
            Tuple[str, int]: A tuple containing the truncated text and the count of tokens used.
        """
        encoding = tiktoken.get_encoding(TOKEN_ENCODING)
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            tokens = tokens[:max_tokens]
        return encoding.decode(tokens), len(tokens)

    def get_embedding(self, text: str, model: str = EMBEDDING_MODEL, max_tokens: int = MAX_TOKENS) -> list[float] | None:
        """Retrieve the embedding vector for a given text, optionally truncating the text to a maximum token count. This function integrates token truncation and embedding generation, providing a single method to handle text inputs for embeddings, especially useful for long texts.

        Args:
            text (str): The text to be embedded.
            model (str): The OpenAI model ID used for generating embeddings.
            max_tokens (int): The maximum number of tokens that the text can be truncated to.

        Returns:
             Union[list[float], None]: The embedding vector obtained from the OpenAI API, or None if unavailable.
        """
        truncated_text, token_count = self.encode_with_truncation(text, max_tokens)
        logger.info(f"Processing text with {token_count} tokens.")
        response = openai.embeddings.create(input=truncated_text, model=model)
        return response.data[0].embedding

    def get_and_save_embeddings(
        data, model: str = EMBEDDING_MODEL, max_tokens: int = MAX_TOKENS, output_file: json = "embedded_rubrics.json"
    ):
        """Retrieve and save embeddings for each article in the data."""
        for rubric_section in data:
            for article in rubric_section["examples"]:
                text = article["summary"]
                truncated_text = self.encode_with_truncation(text, max_tokens)
                response = openai.embeddings.create(input=truncated_text, model=model)
                article["embedding"] = response.data[0].embedding
        with Path.open(output_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def find_most_similar_category(
        self, text: str, embeddings_dict: dict[str, list[float]]
    ) -> tuple[str | None, float | None]:
        """Determine the most similar category for a given text by comparing its embedding to precomputed average embeddings.

        Args:
            text (str): The text to classify.
            embeddings_dict (dict[str, list[float]]): Dictionary of average embeddings by category.

        Returns:
            tuple[Union[str, None], Union[float, None]]: Most similar category and its similarity score, or (None, None) if not found.
        """
        article_embedding = self.get_embedding(text)
        if article_embedding is None:
            return None, None

        similarity_scores = {}
        for category, avg_embedding in embeddings_dict.items():
            similarity_scores[category] = self.cosine_similarity(
                article_embedding, np.array(avg_embedding)
            )

        most_similar_category = max(similarity_scores, key=similarity_scores.get)
        highest_similarity_score = similarity_scores[most_similar_category]
        return most_similar_category, highest_similarity_score
