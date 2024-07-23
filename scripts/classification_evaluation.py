"""Implementation of the Classification Evaluation Module"""

import json
import operator
import tempfile
from collections.abc import Iterator
from pathlib import Path

import mlflow
import numpy as np
from beir.retrieval.evaluation import EvaluateRetrieval
from mlflow import MlflowClient
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, log_loss
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
        self,
        q_rels: dict[str, dict[str, int]],
        results: dict[str, dict[Rubric, float]],
        target_names: list[str],
    ) -> None:
        """Initialization."""
        self.q_rels = q_rels
        self.results = results
        self.target_names = target_names
        self.top_k = [1, 2, 3, 4, 5]

    @property
    def results_values(self) -> dict[str, dict[str, float]]:
        """Results Values."""
        results_values = {}
        for q_id, scores in self.results.items():
            results_values[q_id] = {rubric.value: score for rubric, score in scores.items()}
        return results_values

    @property
    def y_true(self) -> list[str]:
        """Predicted Values."""
        return [next(iter(rel.keys())) for rel in self.q_rels.values()]

    @property
    def y_pred(self) -> list[str]:
        """Predicted Values."""
        return [y_score[0][0] for y_score in self.y_scores]

    @property
    def y_scores(self) -> list[list[tuple[str, float]]]:
        """Predicted Values."""
        y_scores_new = []
        y_scores_copy = self.results.copy()
        for y_score in y_scores_copy.values():
            y_score_items = []
            for key, value in y_score.items():
                y_score_items.append((key.value, value))
            y_score_items.sort(key=operator.itemgetter(1), reverse=True)
            y_scores_new.append(y_score_items)
        return y_scores_new

    def classification_report(self) -> dict[str, float | dict[str, float]]:
        """Classification Report."""
        report: dict[str, float | dict[str, float]] = classification_report(
            self.y_true, self.y_pred, target_names=self.target_names, output_dict=True
        )
        return report

    def confusion_matrix(self) -> ConfusionMatrixDisplay:
        """Confusion Matrix Display."""
        return ConfusionMatrixDisplay.from_predictions(
            self.y_true,
            self.y_pred,
            display_labels=self.target_names,
            cmap="Greens",
            xticks_rotation="vertical",
        )

    def accuracy(self) -> dict[str, float]:
        """Accuracy."""
        classification_report = self.classification_report()
        metric_value: float = classification_report["accuracy"]
        metrics = {"accuracy": metric_value}
        return metrics

    def log_loss(self) -> dict[str, float]:
        """Top K Accuracy Score."""
        metrics = {}
        good_pred = []
        probs = []
        for i, items in enumerate(zip(self.y_true, self.y_scores, strict=True)):
            true_label, labels_scores = items
            for j, label_score in enumerate(labels_scores):
                label, score = label_score
                if label == true_label:
                    probs.append(score)
                    if j == 0:
                        good_pred.append(1)
                    else:
                        good_pred.append(0)
                    break
        log_loss_value = log_loss(good_pred, probs)
        metrics["log_loss"] = log_loss_value
        return metrics

    def macro_avg(self) -> dict[str, float]:
        """Precision."""
        classification_report = self.classification_report()
        metric_values = classification_report["macro avg"]
        metrics = {}
        for metric_name, metric_value in metric_values.items():
            metrics[f"macro_avg_{metric_name}"] = metric_value
        return metrics

    def mean_average_precision_at_k(self) -> dict[str, float]:
        """Mean Average Precision."""
        _, _map, _, _ = EvaluateRetrieval.evaluate(self.q_rels, self.results_values, self.top_k)
        metrics = {}
        for top_k in self.top_k:
            metrics.update({f"map_at_{top_k}": _map[f"MAP@{top_k}"]})
        return metrics

    def recall_at_k(self) -> dict[str, float]:
        """Mean Average Precision."""
        _, _, recall, _ = EvaluateRetrieval.evaluate(self.q_rels, self.results_values, self.top_k)
        metrics = {}
        for top_k in self.top_k:
            metrics.update({f"recall_at_{top_k}": recall[f"Recall@{top_k}"]})
        return metrics

    def precision_at_k(self) -> dict[str, float]:
        """Mean Average Precision."""
        _, _, _, precision = EvaluateRetrieval.evaluate(
            self.q_rels, self.results_values, self.top_k
        )
        metrics = {}
        for top_k in self.top_k:
            metrics.update({f"precision_at_{top_k}": precision[f"P@{top_k}"]})
        return metrics

    def accuracy_at_k(self) -> dict[str, float]:
        """Mean Average Precision."""
        accuracy = EvaluateRetrieval.evaluate_custom(
            self.q_rels, self.results_values, self.top_k, "top_k_acc"
        )
        metrics = {}
        for top_k in self.top_k:
            metrics.update({f"accuracy_at_{top_k}": accuracy[f"Accuracy@{top_k}"]})
        return metrics

    def filtered_out_news_metrics(self) -> dict[str, float]:
        """Filtered Out Metrics."""
        metrics = {}
        classification_report = self.classification_report()
        for metric_name, metric_value in classification_report[Rubric.AUTRE.value].items():
            metrics[f"{Rubric.AUTRE.value}_{metric_name}"] = metric_value
        return metrics

    def metrics(self) -> dict[str, float]:
        """Metrics."""
        metrics = {}
        metrics.update(self.filtered_out_news_metrics())
        metrics.update(self.accuracy())
        metrics.update(self.macro_avg())
        metrics.update(self.mean_average_precision_at_k())
        metrics.update(self.recall_at_k())
        metrics.update(self.precision_at_k())
        metrics.update(self.accuracy_at_k())
        metrics.update(self.log_loss())
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


async def run_experiment(experiment_name: str, run_name: str, vectorstore: Vectorstore) -> None:
    """Run Experiment."""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    target_names = [rubric.value for rubric in Rubric]
    news_classifiers = [MaxMeanNewsClassifier(vectorstore)]
    with mlflow.start_run(run_name=run_name, experiment_id=experiment_id) as parent_run:
        for news_classifier in tqdm(news_classifiers):
            model_name = type(news_classifier).__name__
            with mlflow.start_run(
                run_name=model_name, experiment_id=experiment_id, nested=True
            ) as child_run:
                q_rels = {}
                results = {}
                for i, dataset in tqdm(enumerate(leave_one_out_dataset_generator(vectorstore))):
                    train_news, test_news = dataset
                    q_rels[str(i)] = {test_news[0].rubric.value: 1}
                    ids_to_keep = [Vectorstore.create_uuid(news) for news, _ in train_news]
                    pred = await news_classifier.classify(
                        news=test_news[0], embedding=test_news[1], ids_to_keep=ids_to_keep
                    )
                    results[str(i)] = pred
                run_classification_evaluation(q_rels, results, target_names)
                mlflow.log_param("model", model_name)
                mlflow.log_param("fields", run_name)


def run_classification_evaluation(
    q_rels: dict[str, dict[str, int]],
    results: dict[str, dict[Rubric, float]],
    target_names: list[str],
) -> None:
    """Run Classification Evaluation."""
    classification_evaluation = ClassificationEvaluation(q_rels, results, target_names)
    mlflow.log_metrics(classification_evaluation.metrics())
    classification_report = classification_evaluation.classification_report()
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir, "classification_report.json")
        with path.open("w") as f:
            json.dump(classification_report, f, indent=2)
            mlflow.log_artifact(path)
    fig = classification_evaluation.confusion_matrix().figure_
    mlflow.log_figure(fig, "confusion_matrix.png")


async def main(experiment_name: str, collection_name: str) -> None:
    """Main Function."""
    experiment_name = "cpeq-classification"
    run_name = "title-summary"
    collection_name = "ClassificationEvaluationSummary"
    vectorstore_config = VectorstoreConfig(collection_name=collection_name)

    openai_client = get_openai_client()
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        try:
            vectorstore = Vectorstore(embedding_model, vectorstore_client, vectorstore_config)
            await run_experiment(experiment_name, run_name, vectorstore)
        finally:
            vectorstore_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        main(
            experiment_name="cpeq_classification",
            collection_name="ClassificationEvaluationSummary",
        )
    )
