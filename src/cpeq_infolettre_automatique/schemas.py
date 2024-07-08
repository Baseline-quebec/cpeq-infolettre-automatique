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
    rubric: Annotated[Rubric | None, PlainSerializer(lambda x: x.value if x else None)] = None
    summary: str | None = None

    def to_markdown(self) -> str:
        """Convert the news to markdown."""
        if self.summary is None or self.title is None:
            error_msg = "The news must have a summary and a title to be converted to markdown."
            raise ValueError(error_msg)
        return f"### {self.title}\n\n{self.summary}"


class Newsletter(BaseModel):
    """Schema for the newsletter."""

    news: list[News]
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
        news_per_rubric: dict[Rubric, str] = defaultdict(str)
        for news_item in self.news:
            rubric = news_item.rubric if news_item.rubric is not None else Rubric.AUTRE
            if news_per_rubric.get(rubric) is None:
                news_per_rubric[rubric] = f"## {rubric.value}"
            news_per_rubric[rubric] += f"\n\n{news_item.to_markdown()}"

        non_classified_news = news_per_rubric.pop(Rubric.AUTRE, None)
        return list(news_per_rubric.values()) + (
            [non_classified_news] if non_classified_news else []
        )

    def to_markdown(self) -> str:
        """Convert the newsletter to markdown."""
        newsletter = "\n\n".join([self.header, *self._formatted_news_per_rubric()])
        return newsletter
