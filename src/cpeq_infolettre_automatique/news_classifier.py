"""Implementation of NewsClassifier."""

import operator
import uuid

import numpy as np

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class NewsClassifier:
    """Interface for a news classifier."""

    async def classify(self, news: News) -> Rubric | None:
        """Classify the given news.

        Args:
            news: The news to classify.

        Returns:
            The rubric class of the news
        """
        raise NotImplementedError


class MaxMeanNewsClassifier(NewsClassifier):
    """Classify news based on the maximum mean of the classification scores."""

    def __init__(self, vectorstore: Vectorstore) -> None:
        """Initialize the classifier with the provided Vectorstore.

        Args:
            vectorstore: The Vectorstore to use for classification.
        """
        self.vectorstore = vectorstore

    async def classify(
        self, news: News, ids_to_keep: list[str | uuid.UUID] | None = None
    ) -> Rubric | None:
        """Retrieve Rubric classification scores for a news.

        Args:
            news: The news to classify a new Rubric from.
            ids_to_keep: The list of News ids to keep to perform the the classification.

        Returns:
            list[tuple[Rubric, float]]: A list of tuples containing the Rubric and the classification score.
        """
        news_scores = await self.vectorstore.hybrid_search(news, ids_to_keep)

        if len(news_scores) == 0:
            return None

        scores: dict[Rubric, list[float]] = {Rubric(rubric.value): [] for rubric in Rubric}
        for news_item, score in news_scores:
            if news_item.rubric is not None:
                scores[news_item.rubric].append(score)

        rubric_scores = [
            (rubric, np.mean(score, dtype=float))
            for rubric, score in scores.items()
            if len(score) > 0
        ]

        rubric_scores.sort(key=operator.itemgetter(1), reverse=True)

        return rubric_scores[0][0]
