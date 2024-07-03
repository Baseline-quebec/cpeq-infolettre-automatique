"""Client module for openAI API interaction."""

import logging
import operator
import uuid

import numpy as np
import weaviate
import weaviate.classes as wvc

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.schemas import News


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Vectorstore:
    """Handles vector storage and retrieval using embeddings."""

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        client: weaviate.WeaviateClient,
        vectorstore_config: VectorstoreConfig,
    ) -> None:
        """Initialize the Vectorstore with the provided Weaviate client and collection name.

        Args:
            embedding_model: The embedding model to use for the Vectorstore.
            client: An instance of the Weaviate client to handle API calls.
            collection_name: The name of the collection to store the vectors in.
        """
        self.vectorstore_client = client
        self.embedding_model = embedding_model
        self.collection_name = vectorstore_config.collection_name
        self.top_k = vectorstore_config.top_k
        self.hybrid_weight = vectorstore_config.hybrid_weight

    async def _get_rubric_classification_scores(self, news: News) -> list[tuple[Rubric, float]]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        query: str = self.create_query(news)
        embeddings = await self.embedding_model.embed(text_description=query)

        collection = self.vectorstore_client.collections.get(self.collection_name)

        objects = collection.query.hybrid(
            query=query,
            vector=embeddings,
            limit=self.top_k,
            alpha=self.hybrid_weight,
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
        query = f"{news.title} {news.content}"
        return query

    @staticmethod
    def create_uuid(news: News) -> uuid.UUID:
        """Create a uuid for the news object.

        Args:
            news: The news to create the uuid for.
        """
        return uuid.uuid5(uuid.NAMESPACE_DNS, news.title)

    async def classify_news_rubric(self, news: News) -> Rubric | None:
        """Retrieve classification scores from Weaviate.

        Args:
            news: The news to classify the Rubric for.
        """
        rubric_classification_scores = await self._get_rubric_classification_scores(news)
        if len(rubric_classification_scores) == 0:
            return None
        return rubric_classification_scores[0][0]
