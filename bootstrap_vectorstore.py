"""Script to populate the vectorstore with the reference news."""

import datetime as dt
import json
import uuid as uuid_package
from pathlib import Path

import weaviate
import weaviate.classes as wvc
from tqdm import tqdm

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig, WeaviateConfig
from cpeq_infolettre_automatique.dependencies import get_openai_client
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel, OpenAIEmbeddingModel
from cpeq_infolettre_automatique.schemas import ReferenceNews
from cpeq_infolettre_automatique.vectorstore import VectorStore, get_vectorstore_client


class WeaviateCollection:
    """Weaviate Repository class."""

    def __init__(
        self,
        client: weaviate.WeaviateClient,
        collection_name: str = VectorstoreConfig.collection_name,
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

    def create(self) -> None:
        """Create the collection in Weaviate according to Cpeq News schema. See #TODO for the schema details."""
        self.client.collections.create(
            self.collection_name,
            properties=[
                wvc.config.Property(
                    name="rubric",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=False,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="title",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=False,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="content",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="summary",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    vectorize_property_name=False,
                ),
                wvc.config.Property(
                    name="datetime",
                    data_type=wvc.config.DataType.DATE,
                    index_filterable=True,
                    index_searchable=False,
                    vectorize_property_name=False,
                ),
            ],
        )

    def delete(self) -> None:
        """Delete the collection in Weaviate."""
        self.client.collections.delete(self.collection_name)


def get_reference_news(data_path: Path) -> list[ReferenceNews]:
    """Get the reference news from the data file."""
    with Path.open(data_path) as f:
        data = json.load(f)

    dummy_date = dt.datetime(2024, 1, 2, tzinfo=dt.UTC)  # TODO(olivier.belhumeur): Add dateparser
    reference_news = [
        ReferenceNews(
            title=news_item["title"],
            content=news_item["content"],
            datetime=dummy_date,  # TODO(olivier.belhumeur): Add dateparser
            rubric=Rubric(rubric_group["rubric"]),
            summary=news_item["summary"],
            uuid=uuid_package.uuid5(uuid_package.NAMESPACE_DNS, news_item["title"]),
        )
        for rubric_group in data
        for news_item in rubric_group["examples"]
    ]
    return reference_news


async def populate_db(
    reference_news: list[ReferenceNews],
    weaviate_collection: WeaviateCollection,
    embedding_model: EmbeddingModel,
) -> list[uuid_package.UUID | str]:
    """Create objects in the repository.

    Args:
        data_objects (list[AttributeDataCreate]): The attributes to create.

    Returns:
        str: Status of the create operation.
    """
    uuids_upserted: list[uuid_package.UUID | str] = []
    try:
        with weaviate_collection.client.batch.fixed_size(
            batch_size=weaviate_collection.batch_size,
            concurrent_requests=weaviate_collection.concurrent_requests,
        ) as batch:
            for item in tqdm(reference_news):
                text_to_embed = VectorStore.create_query(item)
                vectorized_item = await embedding_model.embed(text_description=text_to_embed)
                data_object = item.model_dump(exclude={"uuid"})
                uuid_upserted: uuid_package.UUID | str = batch.add_object(
                    properties=data_object,
                    collection=weaviate_collection.collection_name,
                    uuid=item.uuid,
                    vector=vectorized_item,
                )
                uuids_upserted.append(uuid_upserted)
                if batch.number_errors > 0:
                    break
        failed_objs_a = weaviate_collection.client.batch.failed_objects
        if len(weaviate_collection.client.batch.failed_objects) > 0:
            error_msg = f"""Failed to upsert {failed_objs_a[0].object_.properties} objects. Reason: "{failed_objs_a[0].message}"."""
            raise ValueError(error_msg)
    except (
        weaviate.exceptions.UnexpectedStatusCodeError,
        weaviate.exceptions.WeaviateQueryError,
    ) as err:
        raise ValueError(err.message) from err
    return uuids_upserted


async def main() -> None:
    """Populate the vectorstore with the reference news."""
    data_path = Path("rubrics", "rubrics.json")
    reference_news = get_reference_news(data_path)
    for weaviate_client in get_vectorstore_client():
        weavaite_collection = WeaviateCollection(
            weaviate_client, VectorstoreConfig.collection_name
        )
        if weavaite_collection.client.collections.exists(weavaite_collection.collection_name):
            weavaite_collection.delete()
        weavaite_collection.create()

        openai_client = get_openai_client()
        embedding_model = OpenAIEmbeddingModel(openai_client)
        await populate_db(reference_news, weavaite_collection, embedding_model)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
