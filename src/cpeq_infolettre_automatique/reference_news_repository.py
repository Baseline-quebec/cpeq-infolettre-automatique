"""News Repository module."""

import datetime as dt
from typing import TypedDict

import weaviate
import weaviate.classes as wvc

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.schemas import News


class ReferenceNewsType(TypedDict):
    """Schema for the news data.

    Note: This is a TypedDict version of the ReferenceNews schema. It is used to get typed properties from the Weaviate objects.
    """

    title: str
    content: str
    datetime: dt.datetime | None
    rubric: Rubric
    summary: str


class ReferenceNewsRepository:
    """Item Repository class .

    Class that implements CRUD operations for items in a Weaviate vectorstore.
    """

    def __init__(
        self, client: weaviate.WeaviateClient, vectorstore_config: VectorstoreConfig
    ) -> None:
        """Initialize the Reference News Repository.

        Args:
            client: The Weaviate client.
            collection_name: The name of the collection in the vectorstore
        """
        self.client = client
        self.collection_name = vectorstore_config.collection_name

    def read_many_by_rubric(self, rubric: Rubric, nb_per_page: int) -> list[News]:
        """Get objects with specific rubric from the repository.

        Args:
            rubric: The rubric to filter by.
            nb_per_page: The number of objects to return .

        Returns:
            The list of objects with the specified rubric.
        """
        collection = self.client.collections.get(self.collection_name)

        objects = collection.query.fetch_objects(
            filters=wvc.query.Filter.by_property("rubric").equal(rubric.value),
            limit=nb_per_page,
            return_properties=ReferenceNewsType,
        ).objects
        news = [News(**object_.properties) for object_ in objects]
        return news
