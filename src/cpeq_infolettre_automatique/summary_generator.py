"""Implement the news summary generator."""

from inspect import cleandoc

from cpeq_infolettre_automatique.completion_model import CompletionModel
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class SummaryGenerator:
    """Service for summarizing news articles."""

    def __init__(self, completion_model: CompletionModel, vectorstore: Vectorstore) -> None:
        """Initialize the summary generator with the completion model."""
        self.completion_model = completion_model
        self.vectorstore = vectorstore

    async def generate(self, news_to_summarize: News) -> str:
        """Summarize the given news based on reference news exemples.

        Args:
            news_to_summarize: The news to summarize.

        Returns: The summary of the news.
        """
        similar_news = await self.vectorstore.search_similar_news(news_to_summarize)
        if any(news.summary is None for news in similar_news):
            error_msg = "All reference news must have a summary as an exemple."
            raise ValueError(error_msg)

        summary = await self.generate_with_similar_news(news_to_summarize, similar_news)
        return summary

    async def generate_with_similar_news(
        self, news_to_summarize: News, similar_news: list[News]
    ) -> str:
        """Summarize the given news based on reference news exemples.

        Args:
            news: The news to summarize.
            reference_news: The reference news exemples to use for summarization.

        Returns: The summary of the text.
        """
        system_prompt = self.format_system_prompt(similar_news)
        user_message = news_to_summarize.content
        summary = await self.completion_model.complete_message(
            system_prompt=system_prompt, user_message=user_message
        )
        return summary

    @staticmethod
    def format_system_prompt(reference_news: list[News]) -> str:
        """Format the prompt for the OpenAI API.

        Args:
            reference_news: The reference news exemples used to create a prompt for the summarization.

        Returns: The formatted prompt.
        """
        filtered_reference_news = [
            reference_news
            for reference_news in reference_news
            if reference_news.summary and reference_news.content
        ]
        exemples_template = "\n\n".join([
            f"""## Exemple {i + 1}\n\n### Contenu: {exemple.content}\n\n### Résumé: {exemple.summary}"""
            for i, exemple in enumerate(filtered_reference_news)
        ])

        system_prompt = cleandoc("""
            Utilises les articles suivants pour t'inspirer afin de résumer un article. Tu auras accès au contenu des articles d'exemple, ainsi que leurs résumés respectifs.
            # Début des exemples:

            {exemples_template}

            Tu reçeveras en message un contenu d'article à résumer, ne retournes uniquement que le résumer de l'article, sans préfixe avec aucune autre information.""").format(
            exemples_template=exemples_template
        )
        return system_prompt
