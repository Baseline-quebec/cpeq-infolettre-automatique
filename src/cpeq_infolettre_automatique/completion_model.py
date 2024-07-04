"""Completion Models implementation."""

from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from pydantic import BaseModel

from cpeq_infolettre_automatique.config import CompletionModelConfig


class CompletionModel(BaseModel, ABC):
    """Abstract class for completion models."""

    @abstractmethod
    async def complete_message(self, system_prompt: str, user_message: str) -> str:
        """Predict the completion for the given data."""


class OpenAICompletionModel(CompletionModel):
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

    async def complete_message(self, system_prompt: str, user_message: str) -> str:
        """Predict the completion for the given data."""
        chat_response = await self._client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            model=self.model,
        )

        content = chat_response.choices[0].message.content
        if content is None:
            error_msg = "The completion model returned an empty response"
            raise ValueError(error_msg)
        return content
