from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.config import CompletionModelConfig
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.summary_generator import (
    SummaryGenerator,
)


class TestSummaryGenerator:
    @staticmethod
    @pytest.fixture()
    def summary_generator_fixture() -> SummaryGenerator:
        """Fixture for the SummaryGenerator."""
        client = AsyncMock(AsyncOpenAI)
        config_mock = MagicMock(spec=CompletionModelConfig)
        config_mock.model = "mock-model"
        return SummaryGenerator(client, completion_model_config=config_mock)

    @staticmethod
    @pytest.mark.asyncio()
    async def test__summarize_news__when_provided_examples__summarizes_news_effectively(
        summary_generator_fixture: SummaryGenerator, news_fixture: News
    ) -> None:
        """Test the summarize_news method."""
        news_fixture_copy1 = news_fixture.model_copy()
        news_fixture_copy1.summary = "This is a good summary"

        news_fixture_copy2 = news_fixture.model_copy()
        news_fixture_copy2.summary = "This is an excellent summary"

        reference_news = [
            news_fixture_copy1,
            news_fixture_copy2,
        ]
        with patch.object(SummaryGenerator, "_summarize_news", return_value="This is a summary"):
            summary = await summary_generator_fixture.generate(news_fixture, reference_news)
        assert isinstance(summary, str)

    @staticmethod
    def test_format_prompt(
        summary_generator_fixture: SummaryGenerator, news_fixture: News
    ) -> None:
        """Test the format_prompt method."""
        news_fixture_copy1 = news_fixture.model_copy()
        news_fixture_copy1.summary = "This is a good summary"

        news_fixture_copy2 = news_fixture.model_copy()
        news_fixture_copy2.summary = "This is an excellent summary"

        reference_news = [
            news_fixture_copy1,
            news_fixture_copy2,
        ]
        prompt = summary_generator_fixture.format_prompt(news_fixture, reference_news)
        assert isinstance(prompt, str)
