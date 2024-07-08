import datetime as dt

from cpeq_infolettre_automatique.schemas import News, Newsletter


class TestNewsletter:
    @staticmethod
    def test__to_markdown__when_differrent_rubrics__generates_proper_newsletter(
        multiple_summarized_news_fixture: list[News],
        newsletter_fixture: Newsletter,
    ) -> None:
        """Test that the to_markdown method generates a proper markdown formatted newsleter, when more than one of the same rubric, they are grouped toghter."""
        expected_newsletter_content = newsletter_fixture.to_markdown()

        start_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        end_datetime = dt.datetime(2024, 1, 7, tzinfo=dt.UTC)

        newsletter = Newsletter(
            news=multiple_summarized_news_fixture,
            news_datetime_range=(start_datetime, end_datetime),
            publication_datetime=end_datetime,
        )
        newsletter_content = newsletter.to_markdown()
        assert newsletter_content == expected_newsletter_content

    @staticmethod
    def test__to_markdown__when_rubrics_is_none__generates_newsletter_non_classified_at_the_end(
        multiple_summarized_news_with_unclassified_rubric_fixture: list[News],
        newsletter_fixture_with_unclassified_rubric: Newsletter,
    ) -> None:
        """Test that the to_markdown method generates a markdown formatted newsleter with non classified rubric at the end."""
        expected_newsletter_content = newsletter_fixture_with_unclassified_rubric.to_markdown()

        start_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        end_datetime = dt.datetime(2024, 1, 7, tzinfo=dt.UTC)

        newsletter = Newsletter(
            news=multiple_summarized_news_with_unclassified_rubric_fixture,
            news_datetime_range=(start_datetime, end_datetime),
            publication_datetime=end_datetime,
        )
        newsletter_content = newsletter.to_markdown()
        assert newsletter_content == expected_newsletter_content
