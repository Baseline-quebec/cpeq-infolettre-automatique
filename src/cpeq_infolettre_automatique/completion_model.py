"""Completion Models implementation."""

from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, ConfigDict

from cpeq_infolettre_automatique.config import CompletionModelConfig


class CompletionModel(BaseModel, ABC):
    """Abstract class for completion models."""

    completion_model_config: CompletionModelConfig

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def model(self) -> str:
        """Get the model ID."""
        return self.completion_model_config.model

    @property
    def temperature(self) -> float:
        """Get the temperature."""
        return self.completion_model_config.temperature

    @abstractmethod
    async def complete_message(self, user_message: str, system_prompt: str | None) -> str:
        """Predict the completion for the given data."""


class OpenAICompletionModel(CompletionModel):
    """OpenAI completion model implementation."""

    client: AsyncOpenAI

    async def complete_message(self, user_message: str, system_prompt: str | None) -> str:
        """Predict the completion for the given data.

        Args:
            user_message: The user message to complete.
            system_prompt: The system prompt to use for completion, optional.
        """
        messages: list[ChatCompletionMessageParam] = []
        if system_prompt is not None:
            messages.append(ChatCompletionSystemMessageParam(role="system", content=system_prompt))
        messages.append(ChatCompletionUserMessageParam(role="user", content=user_message))

        chat_response = await self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )

        content: str | None = chat_response.choices[0].message.content
        if content is None:
            error_msg = "The completion model returned an empty response"
            raise ValueError(error_msg)
        return content
