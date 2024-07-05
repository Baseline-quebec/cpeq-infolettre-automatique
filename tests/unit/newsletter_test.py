import datetime as dt
from inspect import cleandoc

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.schemas import Newsletter, SummarizedNews


class TestNewsletter:
    @staticmethod
    def test__to_markdown__when_differrent_rubrics__generates_proper_newletter(
        summarized_news_fixture: SummarizedNews,
    ) -> None:
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

        newsletter = Newsletter(news=summarized_news, publication_datetime=fixed_datetime)
        newsletter_content = newsletter.to_markdown
        assert newsletter_content == expected_newsletter
