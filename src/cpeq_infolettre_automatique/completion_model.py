"""Completion Models implementation."""

from abc import ABC, abstractmethod

from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from cpeq_infolettre_automatique.config import CompletionModelConfig


class CompletionModel(BaseModel, ABC):
    """Abstract class for completion models."""

    @abstractmethod
    async def complete_message(self, user_message: str, system_prompt: str | None) -> str:
        """Predict the completion for the given data."""


class OpenAICompletionModel(CompletionModel):
    """OpenAI completion model implementation."""

    def __init__(
        self, client: AsyncOpenAI, completion_model_config: CompletionModelConfig
    ) -> None:
        """Initialize the completion model with the client and configuration.

        Args:
            client: The OpenAI async client.
            completion_model_config: The configuration for the completion model.
        """
        self._client = client
        self.temperature = completion_model_config.temperature
        self.model = completion_model_config.model

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

        chat_response = await self._client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )

        content = chat_response.choices[0].message.content
        if content is None:
            error_msg = "The completion model returned an empty response"
            raise ValueError(error_msg)
        return content
