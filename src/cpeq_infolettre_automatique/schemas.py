"""Schemas used in the application."""

from datetime import datetime

from pydantic import BaseModel


class News(BaseModel):
    """Schema for the news data."""

    title: str
    content: str
    date: datetime | None
    rubric: str | None
    summary: str | None
