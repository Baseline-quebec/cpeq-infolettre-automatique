"""Schemas used in the application."""

import datetime as dt
from inspect import cleandoc
from typing import Annotated, ClassVar

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime


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

    news: list[SummarizedNews]
    publication_datetime: dt.datetime = Field(default_factory=get_current_montreal_datetime)

    def _header(self) -> str:
        """Get the header of the newsletter."""
        newsletter_header = cleandoc("""
            # Infolettre de la CPEQ


            Date de publication: {date}


            Voici les nouvelles de la semaine.""").format(date=self.publication_datetime.date())
        return newsletter_header

    def _formatted_news_per_rubric(self) -> list[str]:
        """Get the formatted news per rubric."""
        news_per_rubric: dict[Rubric, list[SummarizedNews]] = {rubric: [] for rubric in Rubric}
        for news_item in self.news:
            news_per_rubric[news_item.rubric].append(news_item)

        formatted_news_per_rubric: list[str] = []
        for rubric, news_items in news_per_rubric.items():
            if len(news_items) > 0:
                newsletter_rubric_title = f"## {rubric.value}"
                newsletters_rubric_news = "\n\n".join([
                    news_item.to_markdown for news_item in news_items
                ])
                formatted_news_per_rubric.append(
                    f"{newsletter_rubric_title}\n\n{newsletters_rubric_news}"
                )

        return formatted_news_per_rubric

    @property
    def to_markdown(self) -> str:
        """Convert the newsletter to markdown."""
        newsletter_header = self._header()
        formatted_news = "\n\n".join(self._formatted_news_per_rubric())
        newsletter = f"{newsletter_header}\n\n{formatted_news}"
        return newsletter
