"""Implement the NewsRubricClassifier and NewsRelevancyClassifier classes."""

import operator
import uuid
from collections.abc import Sequence
from typing import Any

from cpeq_infolettre_automatique.classification_algo import NewsClassifier
from cpeq_infolettre_automatique.config import NewsRelevancyClassifierConfig, Relevance, Rubric
from cpeq_infolettre_automatique.schemas import News


class NewsRubricClassifier:
    """Implement the NewsClassifier."""

    def __init__(self, model: NewsClassifier) -> None:
        """Initialize the NewsClassifier with the model."""
        self.model = model

    async def predict_probs(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Predict the rubric of the given news.

        Args:
            news: The news to predict the rubric from.

        Returns:
            The rubric classes of the news with their associated probabilities. The results are sorted in descending order of the probabilities.
        """
        return await self.model.predict_probs(news, embedding, ids_to_keep)

    async def predict(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> Rubric:
        """Predict the rubric of the given news.

        Args:
            news: The news to predict the rubric from.

        Returns:
            The rubric class of the news
        """
        predicted_probs = await self.predict_probs(news, embedding, ids_to_keep)
        return Rubric(max(predicted_probs.items(), key=operator.itemgetter(1))[0])

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return f"{type(self).__name__}_{type(self.model).__name__}"

    @property
    def model_info(self) -> dict[str, Any]:
        """Return the model info."""
        return {
            "model_name": self.model_name,
            "classifier": type(self.model).__name__,
            "task": type(self).__name__,
        }


class NewsRelevancyClassifier:
    """Implement the NewsRelevancyClassifier."""

    def __init__(
        self,
        model: NewsClassifier,
        news_relevancy_classifier_config: NewsRelevancyClassifierConfig,
    ) -> None:
        """Initialize the NewsRelevancyClassifier with the model and the configuration."""
        self.model = model
        self.news_relevancy_classifier_config = news_relevancy_classifier_config

    @property
    def threshold(self) -> float:
        """Get the threshold."""
        return self.news_relevancy_classifier_config.threshold

    async def predict(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> Relevance:
        """Predict the relevance of the given news.

        Args:
            news: The news to predict if it is relevant or not.

        Returns:
            The relevance class of the news
        """
        predicted_probs = await self.predict_probs(news, embedding, ids_to_keep)
        return (
            Relevance.PERTINENT
            if predicted_probs[Relevance.PERTINENT.value] >= self.threshold
            else Relevance.AUTRE
        )

    async def predict_probs(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[str, float]:
        """Predict the relevance of the given news.

        Args:
            news: The news to predict if it is relevant or not.

        Returns:
            The relevancy of the news with their associated probabilities. The results are sorted in descending order of the probabilities.
        """
        predicted_probs = await self.model.predict_probs(news, embedding, ids_to_keep)
        not_relevant_prob = predicted_probs[Relevance.AUTRE.value]
        relevant_prob = 1.0 - not_relevant_prob
        probs = {
            Relevance.PERTINENT.value: relevant_prob,
            Relevance.AUTRE.value: not_relevant_prob,
        }
        sorted_probs = dict(sorted(probs.items(), key=operator.itemgetter(1), reverse=True))
        return sorted_probs

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return f"{type(self).__name__}_{type(self.model).__name__}"

    @property
    def model_info(self) -> dict[str, Any]:
        """Return the model info."""
        return {
            "model_name": self.model_name,
            "classifier": type(self.model).__name__,
            "task": type(self).__name__,
            "threshold": self.threshold,
        }
