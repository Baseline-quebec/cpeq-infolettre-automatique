"""Test News Repository."""

import weaviate

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import (
    Vectorstore,
)


class TestReferenceNewsRepository:
    """Test the News Repository."""

    @staticmethod
    def test__read_many_by_rubric__when_only_one_corresponding_rubric__returns_one_rubric(
        embedding_model_fixture: EmbeddingModel,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        vectorstore_config_fixture: VectorstoreConfig,
        summarized_news_fixture: News,
    ) -> None:
        """Test read_many_by_rubric returns proper news with specified rubric when queried with rubric."""
        # Arrange
        vectorstore = Vectorstore(
            embedding_model=embedding_model_fixture,
            vectorstore_client=vectorstore_client_fixture,
            vectorstore_config=vectorstore_config_fixture,
        )
        collection = vectorstore.vectorstore_client.collections.get(vectorstore.collection_name)

        summarized_news_fixture_copy_1 = summarized_news_fixture.model_copy()
        summarized_news_fixture_copy_2 = summarized_news_fixture.model_copy()

        summarized_news_fixture_copy_1.rubric = Rubric.EAU_ET_DOMAINE_MARITIME
        summarized_news_fixture_copy_2.rubric = Rubric.DOMAINE_AGRICOLE
        # Act

        for data in [summarized_news_fixture_copy_1, summarized_news_fixture_copy_2]:
            collection.data.insert(properties=data.model_dump())
        news_by_rubric = vectorstore.read_many_by_rubric(Rubric.DOMAINE_AGRICOLE)
        # Assert
        excepted_news_count = 1
        assert len(news_by_rubric) == excepted_news_count
