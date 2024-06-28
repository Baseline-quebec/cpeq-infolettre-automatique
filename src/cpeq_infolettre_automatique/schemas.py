"""Schemas used in the application."""

import datetime as dt
import uuid as uuid_package
from typing import Any, TypedDict

from pydantic import BaseModel, ConfigDict, field_serializer

from cpeq_infolettre_automatique.config import Rubric


class News(BaseModel):
    """Schema for the news data."""

    title: str
    content: str
    datetime: dt.datetime | None
    rubric: Rubric | None
    summary: str | None

    model_config = ConfigDict(use_enum_values=True)


class ReferenceNews(News):
    """Schema for the reference news data."""

    uuid: uuid_package.UUID
    rubric: Rubric
    datetime: dt.datetime | None

    @staticmethod
    @field_serializer("datetime")
    def serialize_datetime(datetime: dt.datetime, _info: Any) -> str:
        """Serialize the datetime to a isoformat RFC 3339."""
        return datetime.isoformat()


class ReferenceNewsType(TypedDict):
    """Schema for the news data."""

    title: str
    content: str
    datetime: dt.datetime | None
    rubric: Rubric
    summary: str
