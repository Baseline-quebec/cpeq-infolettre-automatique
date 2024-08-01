"""Implementation of NewsClassifier."""

import operator
import uuid
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.special import softmax
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KNeighborsClassifier

from cpeq_infolettre_automatique.config import Rubric, VectorNames
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class NewsClassifier:
    """Interface for a NewsClassifier.

    Note:
        All NewsClassifier implementations should inherit from
        this class and implement the predict and predict_probs method.
        This should only take inputs and outputs, and be agnnostic of the value predicted.
    """

    def __init__(
        self, vectorstore: Vectorstore, *, vector_name: VectorNames, **kwargs: Any
    ) -> None:
        """Initialize the NewsClassifier with the vectorstore.

        Args:
        vectorstore: The vectorstore to use for classification.
        """
        self.vectorstore = vectorstore
        self.vector_name = vector_name

    async def predict_probs(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Predict the rubric of the given news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the news.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            The rubric class of the news with their associated probabilities. Sorted by decreasing probability.
        """
        predicted_scores = await self.predict_scores(news, embedding, ids_to_keep)

        if len(predicted_scores) == 0:
            predicted_scores[Rubric.AUTRE.value] = 1.0

        sorted_probs = dict(
            sorted(predicted_scores.items(), key=operator.itemgetter(1), reverse=True)
        )
        normalized_rubric_scores = self.softmax_scores(sorted_probs)
        return normalized_rubric_scores

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Predict the rubric of the given news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the news.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            The rubric class of the news
        """
        raise NotImplementedError

    def setup(self, train_data: list[tuple[str, list[float]]] | None = None) -> None:
        """Setup the predictor."""

    @staticmethod
    def softmax_scores(scores: dict[str, float]) -> dict[str, float]:
        """Compute the softmax of a list of numbers."""
        softmax_values = softmax(list(scores.values()))
        softmax_scores = dict(zip(scores.keys(), softmax_values, strict=True))
        return softmax_scores


class MaxMeanScoresNewsClassifier(NewsClassifier):
    """Classify news based on the maximum mean of the classification scores."""

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the news.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            The rubric class of the news with their associated probabilities. Sorted by decreasing probability.
        """
        query = Vectorstore.create_query(news, vector_name=self.vector_name)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        news_scores = await self.vectorstore.hybrid_search(
            query, embedding, self.vector_name, ids_to_keep
        )

        predicted_fields = [
            news_item.rubric.value for news_item, _ in news_scores if news_item.rubric is not None
        ]
        list_scores: dict[str, list[float]] = {
            predicted_field: [] for predicted_field in predicted_fields
        }
        for news_item, score in news_scores:
            if news_item.rubric is not None:
                list_scores[news_item.rubric.value].append(score)

        rubric_avg_scores: dict[str, float] = dict.fromkeys(predicted_fields, 0.0)
        for rubric, scores in list_scores.items():
            if len(scores) > 0:
                rubric_avg_scores[rubric] = np.mean(scores, dtype=float)

        return rubric_avg_scores


class MaxScoreNewsClassifier(NewsClassifier):
    """Classify news based on the maximum classification score."""

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the news.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        query = Vectorstore.create_query(news, vector_name=self.vector_name)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        news_scores = await self.vectorstore.hybrid_search(
            query, embedding, self.vector_name, ids_to_keep
        )
        predicted_fields = [
            news_item.rubric.value for news_item, _ in news_scores if news_item.rubric is not None
        ]

        prediction_scores: dict[str, float] = dict.fromkeys(predicted_fields, 0.0)

        for news_item, score in news_scores:
            if news_item.rubric is not None:
                prediction_scores[news_item.rubric.value] = max(
                    prediction_scores[news_item.rubric.value], score
                )

        return prediction_scores


class MaxPoolingNewsClassifier(NewsClassifier):
    """Classify news based on the maximum pooling of the rubric embeddings."""

    def setup(self, train_news: list[tuple[str, list[float]]] | None = None) -> None:
        """Setup the classifier.

        Args:
            train_news: The training data to use for classification.
        """
        if train_news is None:
            news_vectors = self.vectorstore.read_many_with_vectors(vector_name=self.vector_name)
            train_news = [
                (news_vector[0].rubric.value, news_vector[1])
                for news_vector in news_vectors
                if news_vector[0].rubric is not None
            ]
        self.labels = list({train_news_item[0] for train_news_item in train_news})
        labels_embeddings: dict[str, list[list[float]]] = {label: [] for label in self.labels}

        for label, embedding in train_news:
            labels_embeddings[label].append(embedding)

        self.label_average_embeddings = {
            label: np.mean(embeddings, axis=0) for label, embeddings in labels_embeddings.items()
        }

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the item.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        query = Vectorstore.create_query(news, vector_name=self.vector_name)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        label_scores: dict[str, float] = dict.fromkeys(self.labels, 0.0)

        for label, label_embeddings in self.label_average_embeddings.items():
            similarity = cosine_similarity([embedding], [label_embeddings])[0][0]
            label_scores[label] = similarity

        return label_scores


class KnNewsClassifier(NewsClassifier):
    """Classify news based on the K-Nearest Neighbors algorithm."""

    def __init__(
        self,
        vectorstore: Vectorstore,
        vector_name: VectorNames,
        n_neighbors: int = 4,
    ) -> None:
        """Initialize the NewsClassifier with the vectorstore.

        Args:
            vectorstore: The vectorstore to use for classification.
            n_neighbors: The number of neighbors to use for classification.
        """
        super().__init__(vectorstore, vector_name=vector_name)
        self.n_neighbors = n_neighbors
        self.labels: list[str] = []
        self.classifier = KNeighborsClassifier(n_neighbors=self.n_neighbors, metric="cosine")

    def setup(self, train_news: list[tuple[str, list[float]]] | None = None) -> None:
        """Setup the classifier.

        Args:
            train_news: The training data to use for classification.
        """
        if train_news is None:
            news_vectors = self.vectorstore.read_many_with_vectors(self.vector_name)
            train_news = [
                (news_vector[0].rubric.value, news_vector[1])
                for news_vector in news_vectors
                if news_vector[0].rubric is not None
            ]

        x = [train_news_item[1] for train_news_item in train_news]
        y = [train_news_item[0] for train_news_item in train_news]

        self.labels = sorted(set(y))

        self.classifier.fit(x, y)

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            embedding: The embedding of the news.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        query = Vectorstore.create_query(news, vector_name=self.vector_name)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        probs = self.classifier.predict_proba([embedding])

        label_probs = dict(zip(self.labels, probs[0], strict=True))

        return label_probs


class RandomForestNewsClassifier(NewsClassifier):
    """Classify news based on the RandomForest algorithm."""

    def __init__(
        self,
        vectorstore: Vectorstore,
        vector_name: VectorNames,
        n_estimators: int = 100,
    ) -> None:
        """Initialize the NewsClassifier with the vectorstore.

        Args:
            vectorstore: The vectorstore to use for classification.
            n_estimators: The number of estimators to use for classification.
        """
        super().__init__(vectorstore, vector_name=vector_name)
        self.n_estimators = n_estimators
        self.labels: list[str] = []
        self.classifier = RandomForestClassifier(n_estimators=self.n_estimators)

    def setup(self, train_news: list[tuple[str, list[float]]] | None = None) -> None:
        """Setup the classifier."""
        if train_news is None:
            news_vectors = self.vectorstore.read_many_with_vectors(self.vector_name)
            train_news = [
                (news_vector[0].rubric.value, news_vector[1])
                for news_vector in news_vectors
                if news_vector[0].rubric is not None
            ]
        x = [train_news_item[1] for train_news_item in train_news]
        y = [train_news_item[0] for train_news_item in train_news]

        self.labels = sorted(set(y))
        self.classifier.fit(x, y)

    async def predict_scores(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        query = Vectorstore.create_query(news, vector_name=self.vector_name)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        probs = self.classifier.predict_proba([embedding])

        label_probs = dict(zip(self.labels, probs[0], strict=True))

        return label_probs
