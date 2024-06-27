"""Schemas used in the application."""

from datetime import date

from pydantic import BaseModel


class News(BaseModel):
    """Schema for the news data."""

    title: str
    content: str
    date: date | None
    rubric: str | None
    summary: str | None
