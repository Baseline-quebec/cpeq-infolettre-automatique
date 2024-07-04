"""Completion Models implementation."""

from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from pydantic import BaseModel

from cpeq_infolettre_automatique.config import CompletionModelConfig


class CompletionModel(BaseModel, ABC):
    """Abstract class for completion models."""

    @abstractmethod
    async def complete(self, prompt: str) -> str:
        """Predict the completion for the given data."""


class OpenaiCompletionModel(CompletionModel):
    """OpenAI completion model implementation."""

    def __init__(
        self, client: AsyncOpenAI, completion_model_config: CompletionModelConfig
    ) -> None:
        """Initialize the completion model with the client and configuration.

        Args:
            client: The OpenAI client.
            completion_model_config: The configuration for the completion model.
        """
        self._client = client
        self.temperature = completion_model_config.temperature
        self.model = completion_model_config.model

    async def complete(self, prompt: str) -> str:
        """Predict the completion for the given data."""
        response = await self._client.completions.create(
            prompt=prompt,
            model=self.model,
        )
        content = response.choices[0].text
        return content
