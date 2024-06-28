"""Test News Repository."""

import weaviate

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.reference_news_repository import ReferenceNewsRepository
from cpeq_infolettre_automatique.schemas import ReferenceNews


class TestReferenceNewsRepository:
    """Test the News Repository."""

    @staticmethod
    def test_read_many_by_rubric(
        vectorstore_client_fixture: weaviate.WeaviateClient,
        test_collection_name: str,
        reference_news_fixture: ReferenceNews,
    ) -> None:
        """Test the read_many_by_rubric method works with valid data."""
        # Arrange
        news_repository = ReferenceNewsRepository(vectorstore_client_fixture, test_collection_name)
        collection = news_repository.client.collections.get(news_repository.collection_name)

        reference_news_fixture_copy_1 = reference_news_fixture.model_copy()
        reference_news_fixture_copy_2 = reference_news_fixture.model_copy()

        reference_news_fixture_copy_1.rubric = Rubric.EAU_ET_DOMAINE_MARITIME
        reference_news_fixture_copy_2.rubric = Rubric.DOMAINE_AGRICOLE
        # Act

        collection.data.insert(reference_news_fixture_copy_1.model_dump(exclude={"uuid"}))
        collection.data.insert(reference_news_fixture_copy_2.model_dump(exclude={"uuid"}))
        news_by_rubric = news_repository.read_many_by_rubric(Rubric.DOMAINE_AGRICOLE, 2)
        # Assert
        excepted_nb_news = 1
        assert len(news_by_rubric) == excepted_nb_news
