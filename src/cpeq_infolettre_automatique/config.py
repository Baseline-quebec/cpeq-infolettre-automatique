"""Configuration and constants for the web scraping client."""

from typing import ClassVar, Literal

from decouple import config


sitemaps = [
    {"sitemap_id": "some-id"},
]


class EmbeddingModelConfig:
    """Embedding Model dataclass.

    Notes:
    embedding models and info for OpenAI can be found at https://platform.openai.com/docs/guides/embeddings
    """

    embedding_model_id: ClassVar[Literal["text-embedding-3-small", "text-embedding-3-large"]] = (
        "text-embedding-3-large"
    )
    token_encoding: ClassVar[Literal["cl100k_base"]] = "cl100k_base"


class VectorstoreConfig:
    """Configuration for the vector store client."""

    vectorstore_collection: ClassVar[str] = config("WEAVIATE_COLLECTION_NAME", "")


class RetrieverConfig:
    """Retriever Config dataclass."""

    vectorstore_config: ClassVar[VectorstoreConfig] = VectorstoreConfig()
    top_k: ClassVar[int] = int(config("NB_ITEM_RETRIEVED", 5))
    hybrid_weight: ClassVar[float] = 0.75


class WeaviateConfig:
    """Weaviate Config dataclass."""

    query_maximum_results: ClassVar[int] = max(int(config("QUERY_MAXIMUM_RESULTS", 10000)), 1)
    batch_size: ClassVar[int] = max(int(config("BATCH_SIZE", 5)), 1)
    concurrent_requests: ClassVar[int] = max(int(config("CONCURRENT_REQUESTS", 2)), 1)
