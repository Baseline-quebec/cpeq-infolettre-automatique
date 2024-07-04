"""Implements the newsletter generator class."""

from inspect import cleandoc

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
        newsletter_header = cleandoc("""
            # Infolettre de la CPEQ


            Date de publication: {date}


            Voici les nouvelles de la semaine.""").format(
            date=get_current_montreal_datetime().date()
        )

        news_per_rubric: dict[Rubric, list[SummarizedNews]] = {rubric: [] for rubric in Rubric}
        for news_item in summarized_news:
            news_per_rubric[news_item.rubric].append(news_item)

        formated_news_per_rubric = []
        for rubric, news in news_per_rubric.items():
            if news:
                newsletter_rubric_title = f"## {rubric.value}"
                newsletters_rubric_news = "\n\n".join([
                    news_item.to_markdown for news_item in news
                ])
                formated_news_per_rubric.append(
                    f"{newsletter_rubric_title}\n\n{newsletters_rubric_news}"
                )

        newsletter_news = "\n\n".join(formated_news_per_rubric)
        newsletter = f"{newsletter_header}\n\n{newsletter_news}"

        return newsletter
