from cpeq_infolettre_automatique.classification_algorithm import BaseNewsClassifier


class RubricClassifier:
    """Implement the NewsClassifier."""

    def __init__(self, news_classifier: BaseNewsClassifier) -> None:
        """Initialize the RubricClassifier with the provided dependencies."""
        self.news_classifier = news_classifier

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
        predicted_probs = await self.news_classifier.predict_probs(news, embedding, ids_to_keep)
        return Rubric(next(iter(predicted_probs)))

    @property
    def model_name(self) -> str:
        """Return the model name."""
        return f"{type(self).__name__}_{type(self.news_classifier).__name__}"

    @property
    def model_info(self) -> dict[str, Any]:
        """Return the model info."""
        return {
            "model_name": self.model_name,
            "classifier": type(self.news_classifier).__name__,
            "task": type(self).__name__,
        }


class NewsFilterer:
    """Implement the NewsFilterer."""

    def __init__(self, news_classifier: BaseNewsClassifier, threshold: float = 0.50) -> None:
        """Initialize the NewsFilterer with the provided dependencies."""
        self.news_classifier = news_classifier
        self.threshold = threshold

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
        if predicted_probs[Relevance.AUTRE.value] >= self.threshold:
            return Relevance.AUTRE
        return Relevance.PERTINENT

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
            The relevance class of the news
        """
        predicted_probs = await self.news_classifier.predict_probs(news, embedding, ids_to_keep)
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
        return f"{type(self).__name__}_{type(self.news_classifier).__name__}"

    @property
    def model_info(self) -> dict[str, Any]:
        """Return the model info."""
        return {
            "model_name": self.model_name,
            "classifier": type(self.news_classifier).__name__,
            "task": type(self).__name__,
            "threshold": self.threshold,
        }
