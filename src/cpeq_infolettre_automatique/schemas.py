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
    rubric: Rubric | None = None
    summary: str | None = None


class Newsletter(BaseModel):
    """Schema for the Newsletter."""

    text: str
