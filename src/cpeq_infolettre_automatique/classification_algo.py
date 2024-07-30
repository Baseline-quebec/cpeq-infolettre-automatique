"""Implementation of NewsClassifier."""

import operator
import uuid
from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel
from scipy.special import softmax
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import KNeighborsClassifier

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class BaseNewsClassifier(BaseModel):
    """Interface for a NewsClassifier.

    Note:
        All NewsClassifier implementations should inherit from
        this class and implement the predict and predict_probs method.

        This should only take inputs and outputs, and be agnnostic of the value predicted.
    """

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
            The rubric class of the news
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

    def setup(self, train_data: list[tuple[str, list[float]]]) -> None:
        """Setup the predictor."""

    @staticmethod
    def softmax_scores(scores: dict[str, float]) -> dict[str, float]:
        """Compute the softmax of a list of numbers."""
        softmax_values = softmax(list(scores.values()))
        softmax_scores = dict(zip(scores.keys(), softmax_values, strict=True))
        return softmax_scores


class MaxMeanScoresNewsClassifier(BaseNewsClassifier):
    """Classify news based on the maximum mean of the classification scores."""

    def __init__(self, vectorstore: Vectorstore) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
        """
        self.vectorstore = vectorstore

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
        query = Vectorstore.create_query(news)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        news_scores = await self.vectorstore.hybrid_search(query, embedding, ids_to_keep)

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


class MaxScoreNewsClassifier(BaseNewsClassifier):
    """Classify news based on the maximum classification score."""

    def __init__(self, vectorstore: Vectorstore) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
        """
        self.vectorstore = vectorstore

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
        query = Vectorstore.create_query(news)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        news_scores = await self.vectorstore.hybrid_search(query, embedding, ids_to_keep)
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


class KnNewsClassifier(BaseNewsClassifier):
    """Classify news based on the K-Nearest Neighbors algorithm."""

    def __init__(self, vectorstore: Vectorstore, n_neighbors: int = 4) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
            n_neighbors: The number of neighbors to consider for classification.
        """
        self.vectorstore = vectorstore
        self.classifier = KNeighborsClassifier(n_neighbors=n_neighbors, metric="cosine")
        self.labels: list[str] = []

    def setup(self, train_news: list[tuple[str, list[float]]]) -> None:
        """Setup the classifier.

        Args:
            train_news: The training data to use for classification.
        """
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
        query = Vectorstore.create_query(news)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        probs = self.classifier.predict_proba([embedding])

        label_probs = dict(zip(self.labels, probs[0], strict=True))

        return label_probs


class MaxPoolingNewsClassifier(BaseNewsClassifier):
    """Classify news based on the maximum pooling of the rubric embeddings."""

    def __init__(self, vectorstore: Vectorstore) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
        """
        self.vectorstore = vectorstore
        self.labels: list[str] = []

    def setup(self, train_news: list[tuple[str, list[float]]]) -> None:
        """Setup the classifier.

        Args:
            train_news: The training data to use for classification.
        """
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
        query = Vectorstore.create_query(news)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        label_scores: dict[str, float] = dict.fromkeys(self.labels, 0.0)

        for label, label_embeddings in self.label_average_embeddings.items():
            similarity = cosine_similarity([embedding], [label_embeddings])[0][0]
            label_scores[label] = similarity

        return label_scores


class RandomForestNewsClassifier(BaseNewsClassifier):
    """Classify news based on the RandomForest algorithm."""

    def __init__(self, vectorstore: Vectorstore, n_estimators: int = 100) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
            n_estimators: The number of estimators to consider for classification.
        """
        self.vectorstore = vectorstore
        self.classifier = RandomForestClassifier(n_estimators=n_estimators)
        self.labels: list[str] = []

    def setup(self, train_news: list[tuple[str, list[float]]]) -> None:
        """Setup the classifier."""
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
        query = Vectorstore.create_query(news)
        if embedding is None:
            embedding = await self.vectorstore.embedding_model.embed(text_description=query)

        probs = self.classifier.predict_proba([embedding])

        label_probs = dict(zip(self.labels, probs[0], strict=True))

        return label_probs
