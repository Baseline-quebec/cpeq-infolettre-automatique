"""Contains the Embedding classes."""

import tiktoken
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict

from cpeq_infolettre_automatique.config import EmbeddingModelConfig


class EmbeddingModel(BaseModel):
    """Abstract base class for embedding models."""

    embedding_config: EmbeddingModelConfig

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def embedding_model_id(self) -> str:
        """Get the embedding model ID."""
        return self.embedding_config.embedding_model_id

    @property
    def token_encoding(self) -> str:
        """Get the token encoding."""
        return self.embedding_config.token_encoding

    @property
    def max_tokens(self) -> int:
        """Get the maximum number of tokens."""
        return self.embedding_config.max_tokens

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

    client: AsyncOpenAI

    async def embed(self, text_description: str) -> list[float]:
        """Get the embedding of an image or text description.

        Args:
            text_description: The text description.

        Returns:
            The embedding.
        """
        text_description = self.truncate_text(text_description)
        response = await self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text_description,
        )
        embeddings = response.data[0].embedding
        return embeddings

    def truncate_text(self, text: str) -> str:
        """Truncate the text to the maximum token length.

        Args:
            text: The text to truncate.

        Returns:
            The truncated text.
        """
        encoding = tiktoken.get_encoding(self.token_encoding)
        tokens = encoding.encode(text)
        tokens = tokens[: self.max_tokens]
        return encoding.decode(tokens)
