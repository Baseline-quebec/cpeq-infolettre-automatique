"""Implement the news summary generator."""

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
        prompt = self.format_prompt(classified_news, reference_news)
        summarized_news = await self.completion_model.complete(prompt=prompt)
        return summarized_news

    @staticmethod
    def format_prompt(classified_news: ClassifiedNews, reference_news: list[ReferenceNews]) -> str:
        """Format the prompt for the OpenAI API.

        Args:
            text: The text to summarize.

        Returns: The formatted prompt.
        """
        exemples_template = "\n\n".join([
            f"""## Exemple {i + 1}\nContenu: {exemple.content}\nRésumé: {exemple.summary}"""
            for i, exemple in enumerate(reference_news)
        ])

        raw_prompt = f"""Utilises les articles suivants pour t'inspirer afin de résumer un article. Tu auras accès au contenu des articles d'exemple, ainsi que leurs résumés respectifs.
                         #Début des exemples:
                         {exemples_template}

                         #Début du contenu de l'article à résumer:
                         {classified_news.content}"""
        prompt = "\n".join([m.lstrip() for m in raw_prompt.split("\n")])
        return prompt
