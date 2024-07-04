"""Test News Repository."""

import weaviate

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.reference_news_repository import (
    ReferenceNewsRepository,
)
from cpeq_infolettre_automatique.schemas import News


class TestReferenceNewsRepository:
    """Test the News Repository."""

    @staticmethod
    def test__read_many_by_rubric__when_only_one_corresponding_rubric__returns_one_rubric(
        vectorstore_client_fixture: weaviate.WeaviateClient,
        vectorstore_config_fixture: VectorstoreConfig,
        reference_news_fixture: News,
    ) -> None:
        """Test the read_many_by_rubric method works with valid data."""
        # Arrange
        news_repository = ReferenceNewsRepository(
            vectorstore_client_fixture, vectorstore_config_fixture
        )
        collection = news_repository.client.collections.get(news_repository.collection_name)

        reference_news_fixture_copy_1 = reference_news_fixture.model_copy()
        reference_news_fixture_copy_2 = reference_news_fixture.model_copy()

        reference_news_fixture_copy_1.rubric = Rubric.EAU_ET_DOMAINE_MARITIME
        reference_news_fixture_copy_2.rubric = Rubric.DOMAINE_AGRICOLE
        # Act

        for data in [reference_news_fixture_copy_1, reference_news_fixture_copy_2]:
            collection.data.insert(properties=data.model_dump())
        news_by_rubric = news_repository.read_many_by_rubric(Rubric.DOMAINE_AGRICOLE, 2)
        # Assert
        excepted_news_count = 1
        assert len(news_by_rubric) == excepted_news_count
