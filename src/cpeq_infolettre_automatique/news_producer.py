"""Implementation of the News Producer Class."""

from cpeq_infolettre_automatique.news_classifier import NewsRubricClassifier
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator


class NewsProducer:
    """Class to produce news for the newsletter."""

    def __init__(
        self,
        summary_generator: SummaryGenerator,
        news_rubric_classifier: NewsRubricClassifier,
    ) -> None:
        """Initialize the News Producer with the summary generator and the rubric classifier."""
        self.summary_generator = summary_generator
        self.news_rubric_classifier = news_rubric_classifier

    async def produce_news(self, news: News) -> News:
        """Produce the news by classifying and summarizing it."""
        news.summary = await self.summary_generator.generate(news)
        news.rubric = await self.news_rubric_classifier.predict(news)
        return news
