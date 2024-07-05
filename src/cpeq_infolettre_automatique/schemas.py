"""Schemas used in the application."""

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

from cpeq_infolettre_automatique.config import Rubric


class News(BaseModel):
    """Schema for the news data."""

    model_config = ConfigDict(use_enum_values=True)

    title: str
    content: str
    datetime: Annotated[
        dt.datetime | None, PlainSerializer(lambda x: x.isoformat() if x else None)
    ]


class ClassifiedNews(News):
    """Schema for the classified news data."""

    rubric: Rubric


class SummarizedNews(ClassifiedNews):
    """Schema for the summarized news data."""

    summary: str

    @property
    def to_markdown(self) -> str:
        """Convert the news to markdown."""
        return f"### {self.title}\n\n{self.summary}"


class ReferenceNews(SummarizedNews):
    """Schema for the reference news data."""


class Newsletter(BaseModel):
    """Schema for the newsletter."""

    text: str
