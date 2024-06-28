"""Client module for openAI API interaction."""

import logging
import operator
from collections.abc import Iterator

import numpy as np
import weaviate
import weaviate.classes as wvc
from decouple import config

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.schemas import News


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def get_vectorstore_client() -> Iterator[weaviate.WeaviateClient]:
    """Get the vectorstore client.

    Returns:
        weaviate.WeaviateClient: The vectorstore client.
    """
    client: weaviate.WeaviateClient = weaviate.connect_to_embedded(
        version=config("WEAVIATE_VERSION"),
        persistence_data_path=config("WEAVIATE_PERSISTENCE_DATA_PATH"),
    )
    if not client.is_ready():
        error_msg = "Vectorstore is not ready"
        raise ValueError(error_msg)
    yield client
    client.close()


class VectorStore:
    """Handles vector storage and retrieval using embeddings."""

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        client: weaviate.WeaviateClient,
        collection_name: str = VectorstoreConfig.collection_name,
    ) -> None:
        """Initialize the VectorStore with the provided Weaviate client and embedded data.

        Args:
            client: An instance of the Weaviate client to handle API calls.
        """
        self.vectorstore_client = client
        self.embedding_model = embedding_model
        self.collection_name = collection_name

    async def _get_rubric_classification_scores(self, news: News) -> list[tuple[Rubric, float]]:
        """Retrieve data from Weaviate for a specific class .

        Args:
            class_name(str): The name of the class to retrieve
        """
        query: str = self.create_query(news)
        embeddings = await self.embedding_model.embed(text_description=query)

        collection = self.vectorstore_client.collections.get(self.collection_name)

        objects = collection.query.hybrid(
            query=query,
            vector=embeddings,
            limit=VectorstoreConfig.top_k,
            alpha=VectorstoreConfig.hybrid_weight,
            return_metadata=wvc.query.MetadataQuery(score=True),
            return_properties=["rubric", "title", "summary", "content"],
        )

        scores: dict[Rubric, list[float]] = {Rubric(rubric.value): [] for rubric in Rubric}
        for obj in objects.objects:
            scores[Rubric(obj.properties["rubric"])].append(float(obj.metadata.score))  # type: ignore[arg-type]

        rubric_scores = [
            (rubric, np.mean(score, dtype=float))
            for rubric, score in scores.items()
            if len(score) > 0
        ]

        rubric_scores.sort(key=operator.itemgetter(1), reverse=True)

        return rubric_scores

    @staticmethod
    def create_query(news: News) -> str:
        """Create a query for the Weaviate client.

        Args:
            news: The news to create the query for.
        """
        query = f"{news.title} {news.summary} {news.content}"
        return query

    async def classify_news_rubric(self, news: News) -> Rubric | None:
        """Retrieve classification scores from Weaviate.

        Args:
            news: The news to classify the Rubric for.
        """
        rubric_classification_scores = await self._get_rubric_classification_scores(news)
        if len(rubric_classification_scores) == 0:
            return None
        return rubric_classification_scores[0][0]
