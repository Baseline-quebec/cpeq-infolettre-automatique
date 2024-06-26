"""Schemas used in the application."""

import uuid
from datetime import date

from pydantic import BaseModel

from cpeq_infolettre_automatique.config import Rubric


class News(BaseModel):
    """Schema for the news data."""

    title: str
    content: str
    date: date | None
    rubric: Rubric | None
    summary: str | None

    @property
    def query(self) -> str:
        """Query string for the news."""
        return f"{self.title} {self.content}"


class NewsInsert(News):
    """Schema for the news data."""

    @property
    def uuid(self) -> uuid.UUID:
        """UUID of the item."""
        return uuid.uuid5(uuid.NAMESPACE_DNS, self.query)
