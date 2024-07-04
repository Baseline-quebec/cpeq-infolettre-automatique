"""Implements the newsletter generator class."""

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.schemas import SummarizedNews
from cpeq_infolettre_automatique.utils import get_current_montreal_datetime


class NewsletterGenerator:
    """Generates the newsletter."""

    @staticmethod
    def generate_newsletter(summarized_news: list[SummarizedNews]) -> str:
        """Generate the newsletter from the news.

        Args:
            summarized_news: The list of news.

        Returns: The newsletter.
        """
        newsletter = f"""# Infolettre de la CPEQ\n\n
                    Date de publication: {get_current_montreal_datetime().date()}\n\n
                    Voici les nouvelles de la semaine.\n\n"""
        news_per_rubric: dict[Rubric, list[SummarizedNews]] = {rubric: [] for rubric in Rubric}
        for news_item in summarized_news:
            news_per_rubric[news_item.rubric].append(news_item)

        for rubric, news in news_per_rubric.items():
            if news:
                newsletter_for_rubric = f"## {rubric.value}\n\n"
                for news_item in news:
                    newsletter_for_rubric += f"{news_item.to_markdown}\n\n"
                newsletter += newsletter_for_rubric

        return newsletter
