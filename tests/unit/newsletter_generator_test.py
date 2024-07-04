import datetime as dt
from unittest.mock import patch

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.newsletter_generator import NewsletterGenerator
from cpeq_infolettre_automatique.schemas import SummarizedNews


class TestNewsletterGenerator:
    def test_generate_newsletter(self, summarized_news_fixture: SummarizedNews) -> None:
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

        summarized_news = [summarized_news_fixture_copy_1, summarized_news_fixture_copy_2]

        fixed_date = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        expected_newsletter = f"""# Infolettre de la CPEQ\n\n
                    Date de publication: {fixed_date.date()}\n\n
                    Voici les nouvelles de la semaine.\n\n
                    ## {Rubric.ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE.value}\n\n
                    Title 1\n\n
                    Summary 1\n\n
                    Title 3\n\n
                    Summary 3\n\n
                    ## {Rubric.AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME.value}\n\n
                    Title 2\n\n
                    Summary 2\n\n"""

        with patch(
            "cpeq_infolettre_automatique.service.get_current_montreal_datetime"
        ) as get_current_datetime_mock:
            get_current_datetime_mock.return_value = fixed_date

            newsletter = NewsletterGenerator.generate_newsletter(summarized_news)
        assert newsletter == expected_newsletter
