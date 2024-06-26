"""Client module for openAI API interaction."""

import logging
from collections.abc import Iterator
from typing import Any

import weaviate
from decouple import config
from weaviate.classes.aggregate import GroupByAggregate

from cpeq_infolettre_automatique.config import VectorstoreConfig


News = Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_vectorstore_client() -> Iterator[weaviate.WeaviateClient]:
    """Get the vectorstore client.

    Returns:
        weaviate.WeaviateClient: The vectorstore client.
    """
    client: weaviate.WeaviateClient = weaviate.connect_to_embedded(
        headers={"X-OpenAI-Api-key": config("OPENAI_APIKEY")}
    )
    if not client.is_ready():
        error_msg = "Vectorstore is not ready"
        raise ValueError(error_msg)
    yield client
    client.close()


class Vectorstore:
    """Handles vector storage and retrieval using embeddings."""

    def __init__(self, client: weaviate.WeaviateClient) -> None:
        """Initialize the VectorStore with the provided Weaviate client and embedded data.

        Args:
            client (weaviate.WeaviateClient): An instance of the Weaviate client to handle API calls.
        """
        self.vectorstore_client = client

    def _get_classification_scores(self, news: News) -> dict[str, float]:
        """Retrieve data from Weaviate for a specific class.

        Args:
            class_name (str): The name of the class to retrieve
        """
        query: str = news.query

        collection = self.vectorstore_client.collections.get(
            VectorstoreConfig.vectorstore_collection
        )

        objects = collection.aggregate.hybrid(
            query=query, group_by=GroupByAggregate(prop="Rubrique")
        )

        rubrique_scores: dict[str, float] = {}
        for group_rubrique in objects.groups:
            rubrique_scores[group_rubrique.grouped_by.value] = rubrique_scores[
                group_rubrique.grouped_by.value
            ]

        return rubrique_scores

    def get_classification(self, news: News) -> str:
        """Retrieve classification scores from Weaviate.

        Args:
            class_name (str): The name of the class to retrieve
        """
        classification_scores = self._get_classification_scores(news)
        rubrique_with_max_score = max(
            classification_scores, key=lambda k: classification_scores[k]
        )

        return rubrique_with_max_score
