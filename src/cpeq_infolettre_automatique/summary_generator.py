"""Implement the news summary generator."""

from inspect import cleandoc

from cpeq_infolettre_automatique.completion_model import CompletionModel
from cpeq_infolettre_automatique.schemas import ClassifiedNews, ReferenceNews


class SummaryGenerator:
    """Service for summarizing news articles."""

    def __init__(self, completion_model: CompletionModel) -> None:
        """Initialize the service with the client."""
        self.completion_model = completion_model

    async def generate(
        self, classified_news: ClassifiedNews, reference_news: list[ReferenceNews]
    ) -> str:
        """Summarize the given text.

        Args:
            text: The text to summarize.

        Returns: The summary of the text.
        """
        system_prompt = self.format_system_prompt(reference_news)
        user_message = classified_news.content
        summarized_news = await self.completion_model.complete_message(
            system_prompt=system_prompt, user_message=user_message
        )
        return summarized_news

    @staticmethod
    def format_system_prompt(reference_news: list[ReferenceNews]) -> str:
        """Format the prompt for the OpenAI API.

        Args:
            text: The text to summarize.

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

            Tu reçeveras en message un contenu d'article à résumer, ne retournes uniquement que le résumer de l'article, sans préfixe avec aucune autre information.
                         """).format(exemples_template=exemples_template)
        return system_prompt
