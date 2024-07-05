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

        start_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        end_datetime = dt.datetime(2024, 1, 7, tzinfo=dt.UTC)
        expected_newsletter = cleandoc(
            f"""# Infolettre de la CPEQ


               Date de publication: {end_datetime.date()}


               Voici les nouvelles de la semaine du {start_datetime.date()} au {end_datetime.date()}.

               ## {Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE.value}

               ### Title 1

               Summary 1

               ### Title 3

               Summary 3

               ## {Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME.value}

               ### Title 2

               Summary 2"""
        )

        newsletter = Newsletter(
            news=summarized_news,
            news_datetime_range=(start_datetime, end_datetime),
            publication_datetime=end_datetime,
        )
        newsletter_content = newsletter.to_markdown()
        assert newsletter_content == expected_newsletter
