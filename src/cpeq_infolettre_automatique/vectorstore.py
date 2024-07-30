"""Client module for openAI API interaction."""

import datetime as dt
import logging
import uuid
from collections.abc import Sequence
from typing import TypedDict

import weaviate
import weaviate.classes as wvc
from pydantic import ValidationError

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.schemas import News


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ReferenceNewsType(TypedDict):
    """Schema for the news data.

    Note: This is a TypedDict version of the ReferenceNews schema. It is used to get typed properties from the Weaviate objects.
    """

    title: str
    content: str
    link: str
    datetime: dt.datetime | None
    rubric: Rubric
    summary: str


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
        self.max_nb_items_retrieved = vectorstore_config.max_nb_items_retrieved
        self.hybrid_weight = vectorstore_config.hybrid_weight
        self.minimal_score = vectorstore_config.minimal_score

    async def search_similar_news(
        self,
        news: News,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> list[News]:
        """Search for similar news in the vectorstore.

        Args:
            news: The news to search for.
            ids_to_keep: The ids to keep in the search results.

        Returns:
            The list of similar news.
        """
        query = self.create_query(news)
        embeddings = await self.embedding_model.embed(query)
        news_retrieved = await self.hybrid_search(query, embeddings, ids_to_keep)
        return [news_item for news_item, _ in news_retrieved]

    async def hybrid_search(
        self,
        query: str,
        embeddings: list[float],
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> list[tuple[News, float]]:
        collection = self.vectorstore_client.collections.get(self.collection_name)

        objects = collection.query.hybrid(
            query=query,
            vector=embeddings,
            limit=min(self.max_nb_items_retrieved, len(collection)),
            alpha=self.hybrid_weight,
            return_metadata=wvc.query.MetadataQuery(score=True),
            return_properties=ReferenceNewsType,
            filters=wvc.query.Filter.by_id().contains_any(list(ids_to_keep))
            if ids_to_keep
            else None,
        ).objects

        news_retrieved: list[tuple[News, float]] = [
            (News.model_validate(obj.properties), obj.metadata.score)
            for obj in objects
            if obj.metadata.score is not None and obj.metadata.score > self.minimal_score
        ]

        return news_retrieved

    def read_many_by_rubric(self, rubric: Rubric) -> list[News]:
        """Get objects with specific rubric from the repository.

        Args:
            rubric: The rubric to filter by.
            nb_per_page: The number of objects to return .

        Returns:
            The list of objects with the specified rubric.
        """
        collection = self.vectorstore_client.collections.get(self.collection_name)

        objects = collection.query.fetch_objects(
            filters=wvc.query.Filter.by_property("rubric").equal(rubric.value),
            limit=min(self.max_nb_items_retrieved, len(collection)),
            return_properties=ReferenceNewsType,
        ).objects
        news = []
        for object_ in objects:
            try:
                news.append(News.model_validate(object_.properties))
            except ValidationError:
                logging.exception("Error validating object %s", object_)

        return news

    def read_many_with_vectors(self) -> list[tuple[News, list[float]]]:
        """Get objects with specific rubric from the repository.

        Args:
            uuids: The uuids to filter by.

        Returns:
            The list of objects with the specified uuids.
        """
        collection = self.vectorstore_client.collections.get(self.collection_name)

        objects = collection.query.fetch_objects(
            limit=min(self.max_nb_items_retrieved, len(collection)),
            include_vector=True,
            return_properties=ReferenceNewsType,
        ).objects
        news_vectors = []
        for object_ in objects:
            try:
                news_vectors.append((
                    News.model_validate(object_.properties),
                    object_.vector["default"],
                ))
            except ValidationError:
                logging.exception("Error validating object %s", object_)

        return news_vectors

    @staticmethod
    def create_query(news: News) -> str:
        """Create a query for the Weaviate client.

        Args:
            news: The news to create the query for.
        """
        query = f"{news.title} {news.summary}"
        return query

    @staticmethod
    def create_uuid(news: News) -> uuid.UUID:
        """Create a uuid for the news object.

        Args:
            news: The news to create the uuid for.
        """
        return uuid.uuid5(uuid.NAMESPACE_DNS, news.title)
