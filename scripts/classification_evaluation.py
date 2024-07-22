"""Implementation of the Classification Evaluation Module"""

import operator
from collections.abc import Iterator

import mlflow
import numpy as np
from mlflow import MlflowClient
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, top_k_accuracy_score
from tqdm import tqdm

from cpeq_infolettre_automatique.config import Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.dependencies import (
    get_embedding_model,
    get_openai_client,
    get_vectorstore,
    get_vectorstore_client,
)
from cpeq_infolettre_automatique.news_classifier import MaxMeanNewsClassifier, NewsClassifier
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class ClassificationEvaluation:
    """Classification Evaluation Module."""

    def __init__(
        self, y_true: list[str], y_scores: list[list[tuple[str, float]]], target_names: list[str]
    ) -> None:
        """Initialization."""
        self.y_true = y_true
        y_scores_new = []
        y_scores_copy = y_scores.copy()
        for y_score in y_scores_copy:
            y_score.sort(key=operator.itemgetter(1), reverse=True)
            y_scores_new.append(y_score)
        self.y_scores = y_scores_new
        self.target_names = target_names

    @property
    def y_pred(self) -> list[str]:
        """Predicted Values."""
        return [y_score[0][0] for y_score in self.y_scores]

    def classification_report(self) -> dict[str, float]:
        """Classification Report."""
        report: dict[str, float] = classification_report(
            self.y_true, self.y_pred, target_names=self.target_names, output_dict=True
        )
        return report

    def confusion_matrix(self) -> ConfusionMatrixDisplay:
        """Confusion Matrix Display."""
        return ConfusionMatrixDisplay.from_estimator(
            self.y_true,
            self.y_pred,
            display_labels=self.target_names,
            cmap="Greens",
            xticks_rotation="vertical",
        )

    def accuracy(self) -> dict[str, float]:
        """Accuracy."""
        classification_report = self.classification_report()
        metric_value = classification_report["accuracy"]
        return {"accuracy": metric_value}

    def top_k_accuracy_score(self, k: int) -> dict[str, float]:
        """Top K Accuracy Score."""
        top_k_accuracy = top_k_accuracy_score(self.y_true, self.y_scores, k=k, labels=)
        return {f"top_{k}_accuracy": top_k_accuracy}

    def macro_precision(self) -> dict[str, float]:
        """Precision."""
        classification_report = self.classification_report()
        metric_value = classification_report["precision"]
        return {"precision": metric_value}

    def macro_recall(self) -> dict[str, float]:
        """Recall."""
        classification_report = self.classification_report()
        metric_value = classification_report["recall"]
        return {"recall": metric_value}

    def macro_f1_score(self) -> dict[str, float]:
        """F1 Score."""
        classification_report = self.classification_report()
        metric_value = classification_report["f1"]
        return {"f1": metric_value}

    def metrics(self) -> dict[str, float]:
        """Metrics."""
        metrics = {}
        metrics.update(self.accuracy())
        metrics.update(self.macro_precision())
        metrics.update(self.macro_recall())
        metrics.update(self.macro_f1_score())
        metrics.update(self.top_k_accuracy_score(2))
        metrics.update(self.top_k_accuracy_score(3))
        metrics.update(self.top_k_accuracy_score(4))
        metrics.update(self.top_k_accuracy_score(5))
        return metrics


def leave_one_out_dataset_generator(
    vectorstore: Vectorstore,
) -> Iterator[tuple[list[tuple[News, list[float]]], tuple[News, list[float]]]]:
    """Get Dataset."""
    news_vectors = vectorstore.read_many_with_vectors()
    for i in range(len(news_vectors)):
        train_news = news_vectors[:i] + news_vectors[i + 1 :]
        test_news = news_vectors[i]
        yield train_news, test_news


async def run_experiment(experiment_name: str, vectorstore: Vectorstore) -> None:
    """Run Experiment."""
    mlflow.create_experiment(experiment_name)
    target_names = [rubric.value for rubric in Rubric]

    for news_classifier in tqdm([MaxMeanNewsClassifier(vectorstore)]):
        with mlflow.start_run(run_name=type(news_classifier).__name__) as run:
            y_true = []
            y_pred = []
            for dataset in tqdm(leave_one_out_dataset_generator(vectorstore)):
                train_news, test_news = dataset
                y_true.append(test_news[0].rubric.value)
                ids_to_keep = [Vectorstore.create_uuid(news) for news, _ in train_news]
                y_scores = await news_classifier.classify(
                    news=test_news[0], embedding=test_news[1], ids_to_keep=ids_to_keep
                )
                if y_scores is not None:
                    y_pred.append(y_scores.value)
            run_classification_evaluation(y_true, y_pred, target_names)


def run_classification_evaluation(
    y_true: list[str], y_scores: list[list[tuple[str, float]]], target_names: list[str]
) -> None:
    """Run Classification Evaluation."""
    classification_evaluation = ClassificationEvaluation(y_true, y_scores, target_names)
    mlflow.log_metrics(classification_evaluation.metrics())
    classification_report = classification_evaluation.classification_report()
    mlflow.log_artifact(classification_report, "classification_report.json")
    fig = classification_evaluation.confusion_matrix()._figure
    mlflow.log_figure(fig, "confusion_matrix.png")


async def main(experiment_name: str, collection_name: str) -> None:
    """Main Function."""
    experiment_name = "title_summary"
    collection_name = "ClassificationEvaluationSummary"
    vectorstore_config = VectorstoreConfig(collection_name=collection_name)

    openai_client = get_openai_client()
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        vectorstore = Vectorstore(embedding_model, vectorstore_client, vectorstore_config)
        await run_experiment(experiment_name, vectorstore)


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        main(experiment_name="title_summary", collection_name="ClassificationEvaluationSummary")
    )
