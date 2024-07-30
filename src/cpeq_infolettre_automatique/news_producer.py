"""Implementation of the News Producer Class."""

from pydantic import BaseModel, ConfigDict

from cpeq_infolettre_automatique.news_classifier import RubricClassifier
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class NewsProducer(BaseModel):
    """Class to produce news for the newsletter."""

    summary_generator: SummaryGenerator
    rubric_classifier: RubricClassifier
    vectorstore: Vectorstore

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def produce_news(self, news: News) -> News:
        """Produce the news by classifying and summarizing it."""
        reference_news = await self.vectorstore.search_similar_news(news)
        news.summary = await self.summary_generator.generate(news, reference_news)
        news.rubric = await self.rubric_classifier.predict(news)
        return news
