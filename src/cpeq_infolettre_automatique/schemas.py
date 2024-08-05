"""Schemas used in the application."""

import datetime as dt
import unicodedata
from collections import defaultdict
from inspect import cleandoc
from typing import Annotated

from dateparser.search import search_dates
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    UrlConstraints,
    ValidationError,
    field_serializer,
    field_validator,
)
from pydantic_core import Url

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime


class News(BaseModel):
    """Schema for the news data."""

    model_config = ConfigDict(use_enum_values=False, extra="ignore")

    title: str
    content: str
    link: Annotated[Url, UrlConstraints(allowed_schemes=["https"]), PlainSerializer(str)] = Field(
        validation_alias=AliasChoices(
            "link", "articleLink-href", "article-link-href", "article_link-href"
        )
    )
    datetime: dt.datetime | None = Field(validation_alias=AliasChoices("datetime", "date"))
    rubric: Annotated[Rubric | None, PlainSerializer(lambda x: x.value if x else None)] = None
    summary: str | None = None

    @field_validator("link")
    @classmethod
    def valide_link(cls, value: str) -> Url:
        """Validate the link field."""
        try:
            return Url(url=value)
        except ValidationError as e:
            msg = f"Unable to parse article Url {value}."
            raise ValueError(msg) from e

    @field_validator("datetime", mode="before")
    @classmethod
    def validate_datetime(cls, value: dt.datetime | None | str) -> dt.datetime | None:
        """Validate the datetime field."""
        parsed_value = (
            search_dates(
                value,
                settings={
                    "TIMEZONE": "America/Montreal",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )
            if isinstance(value, str)
            else value
        )
        if parsed_value is None or isinstance(parsed_value, dt.datetime):
            return parsed_value
        return parsed_value[0][1]

    @field_serializer("datetime")
    @staticmethod
    def serialize_datetime(datetime: dt.datetime | None) -> str | None:
        """Serialize the datetime field."""
        return datetime.isoformat() if datetime else None

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
        return f"### {self.title}\n\n{self.summary}\n\nPour en connaître davantage, nous vous invitons à consulter cet [hyperlien]({self.link})."


class Newsletter(BaseModel):
    """Schema for the newsletter."""

    news: list[News]
    news_datetime_range: tuple[dt.datetime, dt.datetime]
    publication_datetime: dt.datetime = Field(default_factory=get_current_montreal_datetime)

    @property
    def header(self) -> str:
        """Get the header of the newsletter."""
        newsletter_header = cleandoc(
            f"""
            # Infolettre du CPEQ


            Date de publication: {self.publication_datetime.date()}


            Voici les nouvelles de la semaine du {self.news_datetime_range[0].date()} au {self.news_datetime_range[1].date()}."""
        )
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


class AddNewsBody(BaseModel):
    """Represents the body of the /add-news route."""

    title: str
    link: Annotated[Url, UrlConstraints(allowed_schemes=["https"]), PlainSerializer(str)] = Field(
        validation_alias=AliasChoices("link", "articleLink-href")
    )
    datetime: dt.datetime = Field(validation_alias=AliasChoices("datetime", "date"))
    content: str

    @field_validator("link")
    @classmethod
    def valide_link(cls, value: str) -> Url:
        """Validate the link field."""
        try:
            return Url(url=value)
        except ValidationError as e:
            msg = f"Unable to parse article Url {value}."
            raise ValueError(msg) from e

    @field_validator("datetime", mode="before")
    @classmethod
    def validate_datetime(cls, value: dt.datetime | None | str) -> dt.datetime | None:
        """Validate the datetime field."""
        parsed_value = (
            search_dates(
                value,
                settings={
                    "TIMEZONE": "America/Montreal",
                    "RETURN_AS_TIMEZONE_AWARE": True,
                },
            )
            if isinstance(value, str)
            else value
        )
        if parsed_value is None or isinstance(parsed_value, dt.datetime):
            return parsed_value
        return parsed_value[0][1]

    @field_serializer("datetime")
    @staticmethod
    def serialize_datetime(datetime: dt.datetime) -> str:
        """Serialize the datetime field."""
        return datetime.isoformat()

    @field_validator("title", "content")
    @classmethod
    def validate_mandatory_texts(cls, value: str) -> str:
        """Validate that the mandatory text fields are not empty."""
        if not value.strip() or value is None:
            error_msg = "The title and content fields must not be empty."
            raise ValueError(error_msg)
        cleaned_value = unicodedata.normalize("NFKC", value)
        return cleaned_value

    def to_news(self) -> News:
        """Returns a News domain object from this object's properties."""
        return News(
            title=self.title,
            link=self.link,
            datetime=self.datetime,
            content=self.content,
        )
