"""Implementation of the News Producer Class."""

from cpeq_infolettre_automatique.news_classifier import RubricClassifier
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class NewsProducer:
    """Class to produce news for the newsletter."""

    def __init__(
        self,
        summary_generator: SummaryGenerator,
        news_classifier: RubricClassifier,
        vectorstore: Vectorstore,
    ) -> None:
        """Initialize the NewsProducer with the provided dependencies."""
        self.summary_generator = summary_generator
        self.news_classifier = news_classifier
        self.vectorstore = vectorstore

    async def produce_news(self, news: News) -> News:
        """Produce the news by classifying and summarizing it."""
        reference_news = await self.vectorstore.search_similar_news(news)
        news.summary = await self.summary_generator.generate(news, reference_news)
        news.rubric = await self.news_classifier.predict(news)
        return news
