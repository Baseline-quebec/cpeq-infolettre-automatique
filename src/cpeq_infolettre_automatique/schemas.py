"""Schemas used in the application."""

import datetime as dt
import unicodedata
from collections import defaultdict
from inspect import cleandoc
from typing import Annotated

import dateparser
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    field_validator,
)

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime


CustomDatetime = Annotated[
    dt.datetime | None | str,
    BeforeValidator(
        lambda x: dateparser.parse(
            x,
            settings={"TIMEZONE": "America/Montreal", "RETURN_AS_TIMEZONE_AWARE": True},
        )
        if isinstance(x, str)
        else x,
    ),
    PlainSerializer(lambda x: x.isoformat() if x else None),
]


class News(BaseModel):
    """Schema for the news data."""

    model_config = ConfigDict(use_enum_values=False)

    title: str
    content: str
    datetime: CustomDatetime
    rubric: Annotated[Rubric | None, PlainSerializer(lambda x: x.value if x else None)] = None
    summary: str | None = None

    @field_validator("title", "content")
    @classmethod
    def validate_mandatory_texts(cls, value: str) -> str:
        """Validate that the mandatory text fields are not empty."""
        if not value.strip() or value is None:
            error_msg = "The title and content fields must not be empty."
            raise ValueError(error_msg)
        cleaned_value = unicodedata.normalize("NFKC", value)
        return cleaned_value

    @field_validator("summary")
    @classmethod
    def validate_texts(cls, value: str | None) -> str | None:
        """Validate that the text fields are properly formatted."""
        if value is None:
            return value
        cleaned_value = unicodedata.normalize("NFKC", value)
        return cleaned_value

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
