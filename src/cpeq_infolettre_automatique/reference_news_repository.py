"""News Repository module."""

import weaviate
import weaviate.classes as wvc

from cpeq_infolettre_automatique.config import Rubric, WeaviateConfig
from cpeq_infolettre_automatique.schemas import ReferenceNews, ReferenceNewsType


class ReferenceNewsRepository:
    """Item Repository class.

    Class that implements CRUD operations for items in a Weaviate vectorstore.
    """

    def __init__(self, client: weaviate.WeaviateClient, collection_name: str) -> None:
        """Initialize the repository."""
        self.client = client
        self.collection_name = collection_name
        self.query_maximum_results = WeaviateConfig.query_maximum_results

    def read_many_by_rubric(self, rubic: Rubric, nb_per_page: int) -> list[ReferenceNews]:
        """Get objects from the repository."""
        collection = self.client.collections.get(self.collection_name)

        try:
            objects = collection.query.fetch_objects(
                filters=wvc.query.Filter.by_property("rubric").equal(rubic.value),
                limit=nb_per_page,
                return_properties=ReferenceNewsType,
            ).objects
            reference_news = [
                ReferenceNews(
                    title=data_object.properties["title"],
                    content=data_object.properties["content"],
                    rubric=data_object.properties["rubric"],
                    summary=data_object.properties["summary"],
                    datetime=data_object.properties["datetime"],
                    uuid=data_object.uuid,
                )
                for data_object in objects
            ]

        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
        return reference_news
