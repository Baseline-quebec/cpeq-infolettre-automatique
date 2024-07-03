"""App configuration."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel


EMBEDDING_MODEL: Literal[
    "ext-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
] = "text-embedding-3-large"
TOKEN_ENCODING: Literal["cl100k_base", "p50k_base", "r50k_base", "gpt2"] = "cl100k_base"
MAX_TOKENS: int = 8000

VECTORSTORE_CONTENT_FILEPATH: Path = Path("rubrics", "rubrics.json")


class CompletionModelConfig(BaseModel):
    """Configuration for the completion model."""

    model: Literal["gpt-4o", "gpt-4-turbo"]
    temperature: float = 0.1
