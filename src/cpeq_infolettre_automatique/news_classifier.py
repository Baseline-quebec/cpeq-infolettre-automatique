"""Implementation of NewsClassifier."""

import operator
import uuid
from collections.abc import Sequence

import numpy as np

from cpeq_infolettre_automatique.config import Rubric
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class NewsClassifier:
    """Interface for a news classifier."""

    async def classify(
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[Rubric, float]:
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
        self,
        news: News,
        embedding: list[float] | None = None,
        ids_to_keep: Sequence[str | uuid.UUID] | None = None,
    ) -> dict[Rubric, float]:
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

        if len(news_scores) == 0:
            rubric_scores = dict[Rubric, float] = dict.fromkeys(Rubric, 0.0)
            rubric_scores[Rubric.AUTRE] = 1.0
            return rubric_scores

        rubric_list_scores: dict[Rubric, list[float]] = {rubric: [] for rubric in Rubric}
        for news_item, score in news_scores:
            if news_item.rubric is not None:
                rubric_list_scores[news_item.rubric].append(score)

        rubric_avg_scores: dict[Rubric, float] = dict.fromkeys(Rubric, 0.0)
        for rubric, scores in rubric_list_scores.items():
            if len(scores) > 0:
                rubric_avg_scores[rubric] = np.mean(scores, dtype=float)

        rubric_scores = dict(
            sorted(rubric_avg_scores.items(), key=operator.itemgetter(1), reverse=True)
        )

        return rubric_scores
