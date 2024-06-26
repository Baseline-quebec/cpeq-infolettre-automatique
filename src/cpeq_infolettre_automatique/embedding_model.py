"""Contains the Embedding classes."""

from typing import Annotated

from decouple import config
from fastapi import Depends
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import EmbeddingModelConfig


def get_openai_async_client(api_key: str) -> AsyncOpenAI:
    """Get an asynchronous OpenAI client.

    Args:
        api_key (str): The OpenAI API key.

    Returns:
        AsyncOpenAI: The OpenAI client.
    """
    api_key = config("OPENAI_API_KEY")
    return AsyncOpenAI(api_key=api_key)


class EmbeddingModel:
    """Abstract base class for embedding models."""

    async def embed(self, text_description: str) -> list[float]:
        """Get the embedding of an image or text description.

        Args:
            text_description: The text description.

        Raises:
            NotImplementedError: If the method is not implemented.

        Returns:
            The embedding.
        """
        raise NotImplementedError


class OpenAIEmbeddingModel(EmbeddingModel):
    """Embedding model using OpenAI's API."""

    def __init__(self, client: Annotated[AsyncOpenAI, Depends(get_openai_async_client)]) -> None:
        """Initialize the OpenAIEmbeddingModel."""
        self.client = client
        self.embedding_model_id = EmbeddingModelConfig.embedding_model_id

    async def embed(self, text_description: str) -> list[float]:
        """Get the embedding of an image or text description.

        Args:
            text_description: The text description.

        Returns:
            The embedding.
        """
        # Call OpenAI API to get the embedding
        response = await self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text_description,
        )
        embeddings = response.data[0].embedding
        return embeddings
