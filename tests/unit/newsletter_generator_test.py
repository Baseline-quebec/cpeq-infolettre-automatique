import datetime as dt
from inspect import cleandoc
from unittest.mock import patch

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.newsletter_generator import NewsletterGenerator
from cpeq_infolettre_automatique.schemas import SummarizedNews


class TestNewsletterGenerator:
    @staticmethod
    def test_generate_newsletter(summarized_news_fixture: SummarizedNews) -> None:
        """Test the generate_newsletter method."""
        summarized_news_fixture_copy_1 = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy_1.rubric = (
            Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
        )
        summarized_news_fixture_copy_1.title = "Title 1"
        summarized_news_fixture_copy_1.summary = "Summary 1"

        summarized_news_fixture_copy_2 = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy_2.rubric = Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME
        summarized_news_fixture_copy_2.title = "Title 2"
        summarized_news_fixture_copy_2.summary = "Summary 2"

        summarized_news_fixture_copy_3 = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy_3.rubric = (
            Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE
        )
        summarized_news_fixture_copy_3.title = "Title 3"
        summarized_news_fixture_copy_3.summary = "Summary 3"

        summarized_news = [
            summarized_news_fixture_copy_1,
            summarized_news_fixture_copy_2,
            summarized_news_fixture_copy_3,
        ]

        fixed_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        expected_newsletter = cleandoc(
            """# Infolettre de la CPEQ


               Date de publication: {date}


               Voici les nouvelles de la semaine.

               ## {rubric_1}

               ### Title 1

               Summary 1

               ### Title 3

               Summary 3

               ## {rubric_2}

               ### Title 2

               Summary 2"""
        ).format(
            rubric_1=Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE.value,
            rubric_2=Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME.value,
            date=fixed_datetime.date(),
        )

        with patch(
            "cpeq_infolettre_automatique.newsletter_generator.get_current_montreal_datetime"
        ) as get_current_datetime_mock:
            get_current_datetime_mock.return_value = fixed_datetime

            newsletter = NewsletterGenerator.generate_newsletter(summarized_news)
        assert newsletter == expected_newsletter
