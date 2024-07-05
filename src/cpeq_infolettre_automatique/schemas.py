"""Schemas used in the application."""

import datetime as dt
from collections import defaultdict
from inspect import cleandoc
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime


class News(BaseModel):
    """Schema for the news data."""

    model_config = ConfigDict(use_enum_values=False)

    title: str
    content: str
    datetime: Annotated[
        dt.datetime | None, PlainSerializer(lambda x: x.isoformat() if x else None)
    ]


class ClassifiedNews(News):
    """Schema for the classified news data."""

    rubric: Annotated[Rubric | None, PlainSerializer(lambda x: x.value if x else None)]


class SummarizedNews(ClassifiedNews):
    """Schema for the summarized news data."""

    summary: str

    def to_markdown(self) -> str:
        """Convert the news to markdown."""
        return f"### {self.title}\n\n{self.summary}"


class ReferenceNews(SummarizedNews):
    """Schema for the reference news data."""


class Newsletter(BaseModel):
    """Schema for the newsletter."""

    news: list[SummarizedNews]
    news_datetime_range: tuple[dt.datetime, dt.datetime]
    publication_datetime: dt.datetime = Field(default_factory=get_current_montreal_datetime)

    @property
    def header(self) -> str:
        """Get the header of the newsletter."""
        newsletter_header = cleandoc(f"""
            # Infolettre de la CPEQ


            Date de publication: {self.publication_datetime.date()}


            Voici les nouvelles de la semaine du {self.news_datetime_range[0].date()} au {self.news_datetime_range[1].date()}.""")
        return newsletter_header

    def _formatted_news_per_rubric(self) -> list[str]:
        """Get the formatted news per rubric."""
        news_per_rubric: dict[Rubric, list[SummarizedNews]] = defaultdict(list)
        for news_item in self.news:
            if news_item.rubric is not None:
                news_per_rubric[news_item.rubric].append(news_item)

        formatted_news_per_rubric: list[str] = []
        for rubric, news_items in news_per_rubric.items():
            if len(news_items) > 0:
                newsletter_rubric_title = f"## {rubric.value}"
                newsletters_rubric_news = "\n\n".join([
                    news_item.to_markdown() for news_item in news_items
                ])
                formatted_news_per_rubric.append(
                    f"{newsletter_rubric_title}\n\n{newsletters_rubric_news}"
                )

        return formatted_news_per_rubric

    def to_markdown(self) -> str:
        """Convert the newsletter to markdown."""
        newsletter = "\n\n".join([self.header, *self._formatted_news_per_rubric()])
        return newsletter
