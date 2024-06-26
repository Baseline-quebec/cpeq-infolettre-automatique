"""Client module for openAI API interaction."""

import logging
import operator
from collections.abc import Iterator
from typing import Annotated

import numpy as np
import weaviate
from decouple import config
from fastapi import Depends
from weaviate.classes.aggregate import GroupByAggregate

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.schemas import News


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


class VectorStore:
    """Handles vector storage and retrieval using embeddings."""

    def __init__(
        self, client: Annotated[weaviate.WeaviateClient, Depends(get_vectorstore_client)]
    ) -> None:
        """Initialize the VectorStore with the provided Weaviate client and embedded data.

        Args:
            client: An instance of the Weaviate client to handle API calls.
        """
        self.vectorstore_client = client

    def _get_rubric_classification_scores(self, news: News) -> list[tuple[Rubric, float]]:
        """Retrieve data from Weaviate for a specific class .

        Args:
            class_name(str): The name of the class to retrieve
        """
        query: str = news.query

        collection = self.vectorstore_client.collections.get(
            VectorstoreConfig.vectorstore_collection
        )

        objects = collection.aggregate.hybrid(
            query=query, group_by=GroupByAggregate(prop="rubric")
        )

        rubrique_scores = [
            (Rubric(group_rubrique.grouped_by.value), np.mean([1, 2, 3], dtype=float))
            for group_rubrique in objects.groups
        ]

        rubrique_scores.sort(key=operator.itemgetter(1), reverse=True)

        return rubrique_scores

    async def classify_news_rubric(self, news: News) -> Rubric | None:
        """Retrieve classification scores from Weaviate.

        Args:
            news: The news to classify the Rubric for.
        """
        rubric_classification_scores = self._get_rubric_classification_scores(news)
        if rubric_classification_scores[0][1] > (rubric_classification_scores[1][1] - 0.001):
            return rubric_classification_scores[0][0]

        return None
