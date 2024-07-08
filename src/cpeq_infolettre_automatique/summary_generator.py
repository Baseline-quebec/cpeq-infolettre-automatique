"""Implement the news summary generator."""

from inspect import cleandoc

from cpeq_infolettre_automatique.completion_model import CompletionModel
from cpeq_infolettre_automatique.schemas import News


class SummaryGenerator:
    """Service for summarizing news articles."""

    def __init__(self, completion_model: CompletionModel) -> None:
        """Initialize the SummaryGenerator.

        Args:
            completion_model: The completion model to use for summarization.
        """
        self.completion_model = completion_model

    async def generate(self, classified_news: News, reference_news: list[News]) -> str:
        """Summarize the given news based on reference news exemples.

        Args:
            classified_news: The news to summarize.
            reference_news: The reference news exemples to use for summarization.

        Returns: The summary of the text.
        """
        if classified_news.rubric is None:
            error_msg = "The news must be classified to generate a summary."
            raise ValueError(error_msg)

        if any(news.summary is None for news in reference_news):
            error_msg = "All reference news must have a summary as an exemple."
            raise ValueError(error_msg)

        system_prompt = self.format_system_prompt(reference_news)
        user_message = classified_news.content
        summarized_news = await self.completion_model.complete_message(
            system_prompt=system_prompt, user_message=user_message
        )
        return summarized_news

    @staticmethod
    def format_system_prompt(reference_news: list[News]) -> str:
        """Format the prompt for the OpenAI API.

        Args:
            reference_news: The reference news exemples used to create a prompt for the summarization.

        Returns: The formatted prompt.
        """
        exemples_template = "\n\n".join([
            f"""## Exemple {i + 1}\nContenu: {exemple.content}\nRésumé: {exemple.summary}"""
            for i, exemple in enumerate(reference_news)
        ])

        system_prompt = cleandoc("""
            Utilises les articles suivants pour t'inspirer afin de résumer un article. Tu auras accès au contenu des articles d'exemple, ainsi que leurs résumés respectifs.
            # Début des exemples:
            {exemples_template}

            Tu reçeveras en message un contenu d'article à résumer, ne retournes uniquement que le résumer de l'article, sans préfixe avec aucune autre information.""").format(
            exemples_template=exemples_template
        )
        return system_prompt
