import pytest

from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import (
    SummaryGenerator,
)


class TestSummaryGenerator:
    @staticmethod
    @pytest.mark.asyncio()
    async def test__summarize_news__when_provided_examples__summarizes_news_effectively(
        summary_generator_fixture: SummaryGenerator,
        classified_news_fixture: News,
        summarized_news_fixture: News,
    ) -> None:
        """Test the summarize_news method."""
        summarized_news_fixture_copy = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy.summary = "This is a excellent summary"

        reference_news = [
            summarized_news_fixture,
            summarized_news_fixture_copy,
        ]
        summary = await summary_generator_fixture.generate_with_similar_news(
            classified_news_fixture, reference_news
        )
        assert summary == "Some completion"

    @staticmethod
    def test__format_system_prompt__when_references_news__return_valid_system_prompt(
        summarized_news_fixture: News,
    ) -> None:
        """Test the format_prompt method."""
        summarized_news_fixture_copy = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy.summary = "This is a excellent summary"

        reference_news = [
            summarized_news_fixture,
            summarized_news_fixture_copy,
        ]
        prompt = SummaryGenerator.format_system_prompt(reference_news)
        assert "## Exemple 1\n\n### Contenu:" in prompt
        assert "### Résumé:" in prompt
