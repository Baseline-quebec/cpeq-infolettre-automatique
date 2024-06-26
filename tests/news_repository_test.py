"""Test News Repository."""

import pytest
import weaviate

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.embedding_model import EmbeddingModel
from cpeq_infolettre_automatique.news_repository import NewsRepository
from cpeq_infolettre_automatique.schemas import NewsGet, NewsUpsert


class TestNewsRepository:
    """Test the News Repository."""

    collection_name = "test_collection"

    @pytest.mark.asyncio()
    async def test__create__when_valid_news__should_be_upserted_in_vectorstore(
        self,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        news_upsert_fixture: NewsUpsert,
        embedding_model_fixture: EmbeddingModel,
    ) -> None:
        """Test that create works with the vectorstore."""
        news_repository = NewsRepository(
            vectorstore_client_fixture, embedding_model_fixture, self.collection_name_fixture
        )
        expected_nb_inserted = 1
        uuids_inserted = await news_repository.create([news_upsert_fixture])
        assert len(uuids_inserted) == expected_nb_inserted

    async def test__read__when_upserted_data__should_return_data(
        self,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        news_upsert_fixture: NewsUpsert,
        embedding_model_fixture: EmbeddingModel,
    ) -> None:
        """Test that read works with the vectorstore."""
        # Arrange
        news_repository = NewsRepository(
            vectorstore_client_fixture, embedding_model_fixture, self.collection_name_fixture
        )
        # Act
        _ = news_repository.create([news_upsert_fixture])
        read_items = news_repository.read([news_upsert_fixture.uuid])
        # Assert
        assert all(isinstance(attribute, NewsGet) for attribute in read_items)
        assert read_items[0].uuid == news_upsert_fixture.uuid

    def test_read_many(
        self,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        news_upsert_fixture: NewsUpsert,
        embedding_model_fixture: EmbeddingModel,
    ) -> None:
        """Test the read_many method works with valid data."""
        # Arrange
        news_repository = NewsRepository(
            vectorstore_client_fixture, embedding_model_fixture, self.collection_name
        )
        uuid = news_upsert_fixture.uuid
        # Act
        _ = news_repository.create(
            [news_upsert_fixture],
        )
        news = news_repository.read_many(1, 1)
        # Assert
        assert news[0].uuid == uuid

    def test_read_many_by_rubric(
        self,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        news_upsert_fixture: NewsUpsert,
        embedding_model_fixture: EmbeddingModel,
    ) -> None:
        """Test the read_many_by_rubric method works with valid data."""
        # Arrange
        news_repository = NewsRepository(
            vectorstore_client_fixture, embedding_model_fixture, self.collection_name
        )
        news_upsert_fixture_copy = news_upsert_fixture.model_copy()

        news_upsert_fixture.rubric = Rubric.EAU_ET_DOMAINE_MARITIME
        news_upsert_fixture_copy.rubric = Rubric.DOMAINE_AGRICOLE
        # Act
        _ = news_repository.create(
            [news_upsert_fixture, news_upsert_fixture_copy],
        )
        news_by_rubric = news_repository.read_many_by_rubric(Rubric.DOMAINE_AGRICOLE, 2)
        # Assert
        excepted_nb_news = 1
        assert len(news_by_rubric) == excepted_nb_news

    def test_delete(
        self,
        vectorstore_client_fixture: weaviate.WeaviateClient,
        news_upsert_fixture: NewsUpsert,
        embedding_model_fixture: EmbeddingModel,
    ) -> None:
        """Test the create method with valid data."""
        # Arrange
        news_repository = NewsRepository(
            vectorstore_client_fixture, embedding_model_fixture, self.collection_name
        )
        uuid = news_upsert_fixture.uuid
        data_objects = [news_upsert_fixture]

        # Act
        _ = news_repository.create(data_objects)
        attributes_before_delete = news_repository.read([uuid])
        _ = news_repository.delete([uuid])
        attributes_after_delete = news_repository.read([uuid])

        # Assert
        assert len(attributes_before_delete) == 1
        assert len(attributes_after_delete) == 0
