"""News Repository module."""

import datetime as dt
import logging
from typing import TypedDict

import weaviate
import weaviate.classes as wvc
from pydantic import ValidationError

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.schemas import News


class ReferenceNewsType(TypedDict):
    """Schema for the news data.

    Note: This is a TypedDict version of the ReferenceNews schema. It is used to get typed properties from the Weaviate objects.
    """

    title: str
    content: str
    # link: Url TODO: Add link when updating bootstraping script.
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
        self.nb_items_retrieved = vectorstore_config.nb_items_retrieved

    def read_many_by_rubric(self, rubric: Rubric) -> list[News]:
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
            limit=self.nb_items_retrieved,
            return_properties=ReferenceNewsType,
        ).objects
        news = []
        for object_ in objects:
            try:
                news.append(News.model_validate(object_.properties))
            except ValidationError:
                logging.exception("Error validating object %s", object_)

        return news
