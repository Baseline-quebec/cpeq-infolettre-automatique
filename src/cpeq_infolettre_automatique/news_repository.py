"""News Repository module."""

import uuid
from typing import Any

import weaviate
import weaviate.classes as wvc
from tqdm import tqdm

from cpeq_infolettre_automatique.config import WeaviateConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel


News = Any
NewsInsert = Any
NewsGet = Any


class WeaviateRepository:
    """Weaviate Repository class."""

    def __init__(
        self,
        client: weaviate.WeaviateClient,
        collection_name: str,
        embedding_model: EmbeddingModel,
    ) -> None:
        """Initialize the repository.

        Args:
            client: The Weaviate client.
            collection_name: The collection name.
            embedding_model: The embedding model.
        """
        self.client = client
        self.collection_name = collection_name
        self.query_maximum_results = WeaviateConfig.query_maximum_results
        self.batch_size = WeaviateConfig.batch_size
        self.concurrent_requests = WeaviateConfig.concurrent_requests
        self.embedding_model = embedding_model

        if not self.client.collections.exists(collection_name):
            self.create_collection()

    def create_collection(self) -> None:
        """Create the collection in Weaviate according to Cpeq News schema. See #TODO for the schema details."""
        self.client.collections.create(
            self.collection_name,
            properties=[
                wvc.config.Property(
                    name="unique",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=False,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="uri",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=False,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="title",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="article",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    vectorize_property_name=False,
                ),
            ],
        )

    def delete_collection(self) -> None:
        """Delete the collection in Weaviate."""
        self.client.collections.delete(self.collection_name)


class NewsRepository(WeaviateRepository):
    """Item Repository class.

    Class that implements CRUD operations for items in a Weaviate vectorstore.
    """

    async def create(
        self,
        data_objects: list[NewsInsert],
    ) -> list[str]:
        """Create objects in the repository.

        Args:
            data_objects (list[AttributeDataCreate]): The attributes to create.

        Returns:
            str: Status of the create operation.
        """
        uuids_upserted: list[str] = []
        try:
            with self.client.batch.fixed_size(
                batch_size=self.batch_size,
                concurrent_requests=self.concurrent_requests,
            ) as batch:
                for item in tqdm(data_objects):
                    item.vector = await self.embedding_model.embed(
                        text_description=item.text_to_embed
                    )
                    data_object = item.model_dump(exclude={"vector"})
                    uuid_inserted = batch.add_object(
                        properties=data_object,
                        collection=self.collection_name,
                        uuid=item.uuid,
                        vector=item.vector,
                    )
                    uuids_upserted.append(str(uuid_inserted))
                    if batch.number_errors > 0:
                        break
            failed_objs_a = self.client.batch.failed_objects
            if len(self.client.batch.failed_objects) > 0:
                error_msg = f"""Failed to upsert {failed_objs_a[0].object_.properties} objects. Reason: "{failed_objs_a[0].message}"."""
                raise ValueError(error_msg)
        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
        return uuids_upserted

    def read(self, ids: list[str | uuid.UUID]) -> list[NewsGet]:
        """Get objects from the repository."""
        if len(ids) > self.query_maximum_results:
            error_msg = f"The number of ids to get is too high for the query. Please reduce the number of ids. Limit: {self.query_maximum_results}"
            raise ValueError(error_msg)
        collection = self.client.collections.get(self.collection_name)
        try:
            items_get = [
                NewsGet(**data_object.properties)
                for data_object in collection.query.fetch_objects(
                    filters=wvc.query.Filter.by_id().contains_any(ids),
                    limit=len(ids),
                ).objects
            ]
        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
        return items_get

    def read_many(
        self,
        nb_per_page: int,
        page: int,
    ) -> list[NewsGet]:
        """Get all objects from the repository."""
        collection = self.client.collections.get(self.collection_name)
        offset = (page - 1) * nb_per_page
        try:
            attributes_data = []
            for i, item in enumerate(collection.iterator()):
                if i < offset:
                    continue
                attributes_data.append(NewsGet(**item.properties))
                if (i + 1) == (nb_per_page + offset):
                    break

        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
        return attributes_data

    def delete(self, ids: list[str | uuid.UUID]) -> list[str]:
        """Delete objects from the repository."""
        if len(ids) > self.query_maximum_results:
            error_msg = f"The number of ids to get is too high for the query. Please reduce the number of ids. Limit: {self.query_maximum_results}"
            raise ValueError(error_msg)
        collection = self.client.collections.get(self.collection_name)
        try:
            response = collection.data.delete_many(
                where=wvc.query.Filter.by_id().contains_any(ids), verbose=True
            )
            if len(ids) != response.successful:
                not_deleted_ids = list(
                    set(ids) - {str(object_.id_) for object_ in response.objects}  # type: ignore[attr-defined]
                )
                error_msg = f"Failed to delete {len(not_deleted_ids)}/{len(ids)}. These are the ids that were not deleted: {not_deleted_ids}."
                raise ValueError(error_msg)
        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
        deleted_ids: list[str] = [str(object_.id_) for object_ in response.objects]  # type: ignore[attr-defined]
        return deleted_ids

    def count(self) -> int:
        """Count the number of objects in the collection."""
        try:
            return len(self.client.collections.get(self.collection_name))
        except (
            weaviate.exceptions.UnexpectedStatusCodeError,
            weaviate.exceptions.WeaviateQueryError,
        ) as err:
            raise ValueError(err.message) from err
