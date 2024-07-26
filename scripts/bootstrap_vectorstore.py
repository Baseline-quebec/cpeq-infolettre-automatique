"""Script to populate the vectorstore with the reference news."""

import json
import logging
import uuid
from pathlib import Path

import weaviate
import weaviate.classes as wvc
from tqdm import tqdm

from cpeq_infolettre_automatique.config import (
    EmbeddingModelConfig,
    VectorstoreConfig,
)
from cpeq_infolettre_automatique.dependencies import (
    get_openai_client,
    get_vectorstore_client,
)
from cpeq_infolettre_automatique.embedding_model import (
    EmbeddingModel,
    OpenAIEmbeddingModel,
)
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WeaviateCollection:
    """Weaviate Collection handling class.

    Used to create and delete collections in Weaviate.
    """

    def __init__(
        self,
        client: weaviate.WeaviateClient,
        vectorstore_config: VectorstoreConfig,
    ) -> None:
        """Initialize the repository.

        Args:
            client: The Weaviate client.
            collection_name: The collection name.
            embedding_model: The embedding model.
        """
        self.client = client
        self.collection_name = vectorstore_config.collection_name
        self.batch_size = vectorstore_config.batch_size
        self.concurrent_requests = vectorstore_config.concurrent_requests

    def create(self) -> None:
        """Create the collection in Weaviate according to Cpeq News schema. See #TODO for the schema details."""
        self.client.collections.create(
            self.collection_name,
            properties=[
                wvc.config.Property(
                    name="rubric",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
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
                wvc.config.Property(
                    name="link",
                    data_type=wvc.config.DataType.TEXT,
                    index_filterable=True,
                    index_searchable=True,
                    vectorize_property_name=False,
                ),
            ],
        )

    def delete(self) -> None:
        """Delete the collection in Weaviate."""
        self.client.collections.delete(self.collection_name)


def get_reference_news(data_path: Path) -> list[News]:
    """Get the reference news from the data file."""
    with Path.open(data_path) as f:
        data = json.load(f)

    references_news = [News.model_validate(news_item) for news_item in data]
    return references_news


async def populate_db(
    references_news: list[News],
    weaviate_collection: WeaviateCollection,
    embedding_model: EmbeddingModel,
) -> list[uuid.UUID | str]:
    """Create objects in the repository.

    Args:
        data_objects (list[AttributeDataCreate]): The attributes to create.

    Returns:
        str: Status of the create operation.
    """
    uuids_upserted: list[uuid.UUID | str] = []
    with weaviate_collection.client.batch.fixed_size(
        batch_size=weaviate_collection.batch_size,
        concurrent_requests=weaviate_collection.concurrent_requests,
    ) as batch:
        for reference_news in tqdm(references_news):
            if reference_news.rubric is None:
                logger.warning("Reference News with title %s had no rubric.", reference_news.title)
                continue
            text_to_embed = Vectorstore.create_query(reference_news)
            object_id = Vectorstore.create_uuid(reference_news)
            vectorized_item = await embedding_model.embed(text_description=text_to_embed)
            uuid_upserted: uuid.UUID | str = batch.add_object(
                properties=reference_news.model_dump(),
                collection=weaviate_collection.collection_name,
                uuid=object_id,
                vector=vectorized_item,
            )
            uuids_upserted.append(uuid_upserted)
            if batch.number_errors > 0:
                break
    failed_objs_a = weaviate_collection.client.batch.failed_objects
    if len(weaviate_collection.client.batch.failed_objects) > 0:
        error_msg = f"""Failed to upsert {failed_objs_a[0].object_.properties} objects. Reason: "{failed_objs_a[0].message}"."""
        raise ValueError(error_msg)
    return uuids_upserted


def upsert_vectorstore_collection(weaviate_collection: WeaviateCollection) -> None:
    """Recreate the collection in Weaviate according to Cpeq News schema."""
    if weaviate_collection.client.collections.exists(weaviate_collection.collection_name):
        weaviate_collection.delete()
    weaviate_collection.create()


async def bootstrap_vectorstore(
    reference_news: list[News],
    weaviate_collection: WeaviateCollection,
    embedding_model: EmbeddingModel,
    *,
    recreate_vectorstore_collection: bool = True,
) -> None:
    """Populate the vectorstore with the reference news."""
    if recreate_vectorstore_collection:
        upsert_vectorstore_collection(weaviate_collection)
    await populate_db(reference_news, weaviate_collection, embedding_model)


async def main() -> None:
    """Populate the vectorstore with the reference news."""
    data_path = Path("data", "reference_news", "reference_news_combined.json")
    reference_news = get_reference_news(data_path)
    openai_client = get_openai_client()
    embedding_model_config = EmbeddingModelConfig()
    embedding_model = OpenAIEmbeddingModel(openai_client, embedding_model_config)
    vectorstore_config = VectorstoreConfig(collection_name="ClassificationEvaluationContent")
    for weaviate_client in get_vectorstore_client():
        weaviate_collection = WeaviateCollection(weaviate_client, vectorstore_config)
        await bootstrap_vectorstore(
            reference_news,
            weaviate_collection,
            embedding_model,
            recreate_vectorstore_collection=True,
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
