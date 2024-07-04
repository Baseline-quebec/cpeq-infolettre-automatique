import pytest

from cpeq_infolettre_automatique.schemas import ClassifiedNews, ReferenceNews
from cpeq_infolettre_automatique.summary_generator import (
    SummaryGenerator,
)


class TestSummaryGenerator:
    @staticmethod
    @pytest.mark.asyncio()
    async def test__summarize_news__when_provided_examples__summarizes_news_effectively(
        summary_generator_fixture: SummaryGenerator,
        classified_news_fixture: ClassifiedNews,
        reference_news_fixture: ReferenceNews,
    ) -> None:
        """Test the summarize_news method."""
        reference_news_fixture_copy = reference_news_fixture.model_copy()
        reference_news_fixture_copy.summary = "This is a excellent summary"

        reference_news = [
            reference_news_fixture,
            reference_news_fixture_copy,
        ]
        summary = await summary_generator_fixture.generate(classified_news_fixture, reference_news)
        assert isinstance(summary, str)

    @staticmethod
    def test__format_system_prompt__when_references_news__return_valid_system_prompt(
        summary_generator_fixture: SummaryGenerator,
        reference_news_fixture: ReferenceNews,
    ) -> None:
        """Test the format_prompt method."""
        reference_news_fixture_copy = reference_news_fixture.model_copy()
        reference_news_fixture_copy.summary = "This is a excellent summary"

        reference_news = [
            reference_news_fixture,
            reference_news_fixture_copy,
        ]
        prompt = summary_generator_fixture.format_system_prompt(reference_news)
        assert isinstance(prompt, str)
