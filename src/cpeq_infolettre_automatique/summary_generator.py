"""Implement the news summary generator."""

from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import CompletionModelConfig
from cpeq_infolettre_automatique.schemas import News


ClassifiedNews = News
ReferenceNews = News


class SummaryGenerator:
    """Service for summarizing news articles."""

    def __init__(
        self, client: AsyncOpenAI, completion_model_config: CompletionModelConfig
    ) -> None:
        """Initialize the service with the client."""
        self._client = client
        self.model = completion_model_config.model

    async def generate(
        self, classified_news: ClassifiedNews, reference_news: list[ReferenceNews]
    ) -> str:
        """Summarize the given text.

        Args:
            text: The text to summarize.

        Returns: The summary of the text.
        """
        prompt = self.format_prompt(classified_news, reference_news)
        summarized_news = await self._generate(prompt=prompt)
        return summarized_news

    async def _generate(self, prompt: str) -> str:
        summarized_news_response = await self._client.completions.create(
            prompt=prompt,
            model=self.model,
        )
        summarized_news_response_content = summarized_news_response.choices[0].text
        return summarized_news_response_content

    @staticmethod
    def format_prompt(classified_news: ClassifiedNews, reference_news: list[ReferenceNews]) -> str:
        """Format the prompt for the OpenAI API.

        Args:
            text: The text to summarize.

        Returns: The formatted prompt.
        """
        exemples_template = "\n\n".join([
            f"Exemple {i + 1}: {exemple.content}\nRésumé {i + 1}"
            for i, exemple in enumerate(reference_news)
        ])

        prompt = f"""Utilises les articles suivants pour t'inspirer afin de résumer un article. Tu auras accès au contenu des articles d'exemple, ainsi que leurs résumés respectifs.
                    #Début des exemples:
                    {exemples_template}

                    #Début de l'article à résumer:
                    {classified_news.content}"""
        return prompt
