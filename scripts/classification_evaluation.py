"""Implementation of the Classification Evaluation Module."""

import json
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import mlflow
import pandas as pd
from beir.retrieval.evaluation import EvaluateRetrieval
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    classification_report,
    log_loss,
)
from tqdm import tqdm

from cpeq_infolettre_automatique.classification_algo import (
    KnNewsClassifier,
    MaxMeanScoresNewsClassifier,
    MaxPoolingNewsClassifier,
    MaxScoreNewsClassifier,
)
from cpeq_infolettre_automatique.config import (
    NewsRelevancyClassifierConfig,
    Relevance,
    Rubric,
    VectorNames,
    VectorstoreConfig,
)
from cpeq_infolettre_automatique.dependencies import (
    get_embedding_model,
    get_openai_client,
    get_vectorstore_client,
)
from cpeq_infolettre_automatique.news_classifier import (
    NewsRelevancyClassifier,
    NewsRubricClassifier,
)
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class ClassificationEvaluation:
    """Classification Evaluation Module."""

    def __init__(
        self,
        q_rels: dict[str, dict[str, int]],
        results: dict[str, dict[str, float]],
        y_pred: list[str],
        target_names: list[str],
    ) -> None:
        """Initialization."""
        self.q_rels = q_rels
        self.results = results
        self.y_pred = y_pred
        self.target_names = target_names
        self.top_k = [1, 2, 3, 4, 5]

    @property
    def results_values(self) -> dict[str, dict[str, float]]:
        """Results Values."""
        results_values = {}
        for q_id, scores in self.results.items():
            results_values[q_id] = dict(scores.items())
        return results_values

    @property
    def y_true(self) -> list[str]:
        """Predicted Values."""
        return [next(iter(rel.keys())) for rel in self.q_rels.values()]

    @property
    def y_scores(self) -> list[list[tuple[str, float]]]:
        """Predicted Values."""
        y_scores_new = []
        y_scores_copy = self.results.copy()
        for y_score in y_scores_copy.values():
            y_score_items = []
            for key, value in y_score.items():
                y_score_items.append((key, value))
            y_score_items.sort(key=lambda rubric_prob: rubric_prob[1], reverse=True)
            y_scores_new.append(y_score_items)
        return y_scores_new

    def classification_report(self) -> dict[str, float | dict[str, float]]:
        """Classification Report."""
        report: dict[str, float | dict[str, float]] = classification_report(
            self.y_true, self.y_pred, output_dict=True, labels=self.target_names
        )
        return report

    def classification_report_txt(self) -> str:
        """Classification Report txt."""
        report: str = classification_report(self.y_true, self.y_pred, output_dict=False)
        return report

    def confusion_matrix(self) -> ConfusionMatrixDisplay:
        """Confusion Matrix Display."""
        return ConfusionMatrixDisplay.from_predictions(
            self.y_true,
            self.y_pred,
            cmap="Greens",
            xticks_rotation="vertical",
            display_labels=self.target_names,
        )

    def roc_curve(self) -> ConfusionMatrixDisplay:
        """Confusion Matrix Display."""
        autre_preds_scores = []
        for scores in self.y_scores:
            for label, score in scores:
                if label == Relevance.AUTRE.value:
                    autre_preds_scores.append(score)
        return RocCurveDisplay.from_predictions(
            [int(true_pred == "Autre") for true_pred in self.y_true],
            autre_preds_scores,
            name=f"{Relevance.AUTRE.value} vs the rest",
            color="darkorange",
        )

    def classification_accuracy(self) -> dict[str, float]:
        """Accuracy."""
        classification_report = self.classification_report()
        metric_value: float = classification_report["accuracy"]  # type: ignore[assignment]
        metrics = {"classification_accuracy": metric_value}
        return metrics

    def log_loss(self) -> dict[str, float]:
        """Top K Accuracy Score."""
        metrics = {}
        good_pred = []
        probs = []
        for items in zip(self.y_true, self.y_scores, strict=True):
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
        for metric_name, metric_value in metric_values.items():  # type: ignore[union-attr]
            metrics[f"macro_avg_{metric_name}"] = metric_value
        return metrics

    def classification_metrics(self) -> dict[str, float]:
        """Classification Metrics."""
        classification_metrics = {}
        classification_metrics.update(self.filtered_out_news_metrics())
        classification_metrics.update(self.classification_accuracy())
        classification_metrics.update(self.macro_avg())
        classification_metrics.update(self.log_loss())
        return classification_metrics

    def retriever_metrics(self) -> list[dict[str, float]]:
        """Retriever Metrics."""
        retriever_metrics: list[dict[str, float]] = []
        retriever_metrics.extend((
            self.mean_average_precision_at_k(),
            self.recall_at_k(),
            self.precision_at_k(),
            self.accuracy_at_k(),
        ))
        return retriever_metrics

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
        for metric_name, metric_value in classification_report[Relevance.AUTRE.value].items():  # type: ignore[union-attr]
            metrics[f"{Relevance.AUTRE.value}_{metric_name}"] = metric_value
        return metrics

    def metrics(self) -> dict[str, float]:
        """Metrics."""
        metrics = {}
        metrics.update(self.classification_accuracy())
        metrics.update(self.macro_avg())
        metrics.update(self.mean_average_precision_at_k())
        metrics.update(self.recall_at_k())
        metrics.update(self.precision_at_k())
        metrics.update(self.accuracy_at_k())
        metrics.update(self.log_loss())
        return metrics


def leave_one_out_rubric_classification_dataset_generator(
    vectorstore: Vectorstore,
    *,
    vector_name: VectorNames,
) -> Iterator[tuple[list[tuple[News, str, list[float]]], tuple[News, str, list[float]]]]:
    """Get Dataset."""
    news_vectors = vectorstore.read_many_with_vectors(vector_name=vector_name)
    for i in range(len(news_vectors)):
        train_news_vector = news_vectors[:i] + news_vectors[i + 1 :]
        train_news_class_vector = [
            (news, news.rubric.value if news.rubric is not None else Rubric.AUTRE.value, vector)
            for news, vector in train_news_vector
        ]
        test_news_vector = news_vectors[i]
        test_news_class_vector = (
            test_news_vector[0],
            test_news_vector[0].rubric.value
            if test_news_vector[0].rubric is not None
            else Rubric.AUTRE.value,
            test_news_vector[1],
        )
        yield train_news_class_vector, test_news_class_vector


def leave_one_out_news_filtering_dataset_generator(
    vectorstore: Vectorstore,
    *,
    vector_name: VectorNames,
) -> Iterator[tuple[list[tuple[News, str, list[float]]], tuple[News, str, list[float]]]]:
    """Get Dataset."""
    news_vectors = vectorstore.read_many_with_vectors(vector_name=vector_name)
    for i in range(len(news_vectors)):
        train_news_vector = news_vectors[:i] + news_vectors[i + 1 :]
        train_news_class_vector = [
            (
                news,
                Relevance.AUTRE.value
                if news.rubric == Rubric.AUTRE
                else Relevance.PERTINENT.value,
                vector,
            )
            for news, vector in train_news_vector
        ]
        test_news_vector = news_vectors[i]
        test_news_class_vector = (
            test_news_vector[0],
            Relevance.AUTRE.value
            if test_news_vector[0].rubric == Rubric.AUTRE
            else Relevance.PERTINENT.value,
            test_news_vector[1],
        )
        yield train_news_class_vector, test_news_class_vector


async def run_classifiers_experiment(  # noqa: PLR0914
    experiment_type: Literal["rubric-classification", "news-filtering"],
    run_type: VectorNames,
    news_classifiers: list[NewsRelevancyClassifier | NewsRubricClassifier],
    vectorstore: Vectorstore,
) -> None:
    """Run Experiment."""
    if experiment_type == "rubric-classification":
        target_names = [rubric.value for rubric in Rubric]
    else:
        target_names = [relevance.value for relevance in Relevance]
    target_names.sort()

    experiment_name = f"cpeq-{experiment_type}"

    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    parent_run = mlflow.search_runs(
        experiment_ids=[experiment_id], filter_string=f"run_name='{run_type.value}'"
    )
    parent_run_id = None
    if not parent_run.empty:
        parent_run_id = parent_run["run_id"][0]
    with mlflow.start_run(
        run_id=parent_run_id, run_name=run_type.value, experiment_id=experiment_id
    ) as parent_run:
        for news_classifier in tqdm(news_classifiers):
            with mlflow.start_run(
                experiment_id=experiment_id,
                nested=True,
            ) as child_run:  # noqa: F841
                q_rels = {}
                results = {}
                y_pred = []
                wrong_preds: list[tuple[str, dict[str, dict[str, float]]]] = []
                dataset_generator = (
                    leave_one_out_rubric_classification_dataset_generator
                    if experiment_type == "rubric-classification"
                    else leave_one_out_news_filtering_dataset_generator
                )
                for i, dataset in tqdm(
                    enumerate(dataset_generator(vectorstore, vector_name=run_type))
                ):
                    train_news_class_vector, test_news_class_vector = dataset
                    test_news, test_class, test_embedding = test_news_class_vector
                    ids_to_keep = [
                        Vectorstore.create_uuid(news) for news, _, _ in train_news_class_vector
                    ]
                    train_class_vector = [
                        (class_, embedding) for _, class_, embedding in train_news_class_vector
                    ]
                    news_classifier.model.setup(train_class_vector)
                    q_rels[str(i)] = {test_class: 1}
                    probs = await news_classifier.predict_probs(
                        news=test_news, embedding=test_embedding, ids_to_keep=ids_to_keep
                    )
                    results[str(i)] = probs
                    prediction = await news_classifier.predict(
                        news=test_news, embedding=test_embedding, ids_to_keep=ids_to_keep
                    )
                    y_pred.append(prediction.value)
                    if prediction.value != test_class:
                        wrong_preds.append((
                            test_news.title,
                            {
                                "actual": {test_class: probs.get(test_class, 0.0)},
                                "pred": {prediction.value: probs[prediction.value]},
                            },
                        ))

                run_classification_evaluation(q_rels, results, y_pred, target_names, wrong_preds)
                mlflow.log_params(news_classifier.model_info)
                mlflow.log_param("fields", run_type.value)


def run_classification_evaluation(
    q_rels: dict[str, dict[str, int]],
    results: dict[str, dict[str, float]],
    y_pred: list[str],
    target_names: list[str],
    wrong_preds: list[tuple[str, dict[str, dict[str, float]]]],
) -> None:
    """Run Classification Evaluation."""
    classification_evaluation = ClassificationEvaluation(q_rels, results, y_pred, target_names)
    mlflow.log_metrics(classification_evaluation.classification_metrics())
    retriever_metrics = classification_evaluation.retriever_metrics()
    for metrics in retriever_metrics:
        for key, value in metrics.items():
            new_key = key.split("_")[0]
            k = int(key.split("_")[-1])
            mlflow.log_metric(new_key, value, step=k)
    classification_report = classification_evaluation.classification_report()
    mlflow.log_table(
        pd.DataFrame.from_dict(classification_report)
        .T.reset_index()
        .rename({"index": "field"}, axis=1),
        "classification_report.json",
    )
    classification_report_txt: str = classification_evaluation.classification_report_txt()
    with tempfile.TemporaryDirectory() as tmp_dir:
        wrong_preds_json_path = Path(tmp_dir, "wrong_preds.json")
        with wrong_preds_json_path.open("w", encoding="utf-8") as f:
            json.dump(wrong_preds, f, indent=2, ensure_ascii=False)

        txt_path = Path(tmp_dir, "classification_report.txt")
        txt_path.write_text(classification_report_txt)

        mlflow.log_artifacts(tmp_dir)

    fig = classification_evaluation.confusion_matrix().figure_

    mlflow.log_figure(fig, "confusion_matrix.png", save_kwargs={"bbox_inches": "tight"})

    fig = classification_evaluation.roc_curve().figure_

    mlflow.log_figure(fig, "roc_curve.png", save_kwargs={"bbox_inches": "tight"})


async def prepare_news_classifiers_experiment(
    experiment_type: Literal["rubric-classification", "news-filtering"],
    run_type: VectorNames,
    collection_name: str,
) -> None:
    """Main Function."""
    vectorstore_config = VectorstoreConfig(collection_name=collection_name)

    openai_client = get_openai_client()
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        try:
            vectorstore = Vectorstore(
                embedding_model=embedding_model,
                vectorstore_client=vectorstore_client,
                vectorstore_config=vectorstore_config,
            )
            news_classifier_models = [
                MaxMeanScoresNewsClassifier(vectorstore=vectorstore, vector_name=run_type),
                KnNewsClassifier(vectorstore=vectorstore, vector_name=run_type),
                MaxScoreNewsClassifier(vectorstore=vectorstore, vector_name=run_type),
                MaxPoolingNewsClassifier(vectorstore=vectorstore, vector_name=run_type),
            ]

            news_classifiers: list[NewsRubricClassifier | NewsRelevancyClassifier] = []
            if experiment_type == "rubric-classification":
                news_classifiers.extend([
                    NewsRubricClassifier(model=model) for model in news_classifier_models
                ])

            elif experiment_type == "news-filtering":
                for news_classifier in news_classifier_models:
                    for threshold in [0.3, 0.45, 0.4, 0.45, 0.5]:
                        news_classifiers.append(  # noqa: PERF401
                            NewsRelevancyClassifier(
                                model=news_classifier,
                                news_relevancy_classifier_config=NewsRelevancyClassifierConfig(
                                    threshold=threshold
                                ),
                            )
                        )
            await run_classifiers_experiment(
                experiment_type, run_type, news_classifiers, vectorstore
            )
        finally:
            vectorstore_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        prepare_news_classifiers_experiment(
            experiment_type="rubric-classification",
            run_type=VectorNames.TITLE_SUMMARY,
            collection_name="ClassificationEvaluation",
        )
    )
    asyncio.run(
        prepare_news_classifiers_experiment(
            experiment_type="rubric-classification",
            run_type=VectorNames.TITLE_CONTENT,
            collection_name="ClassificationEvaluation",
        )
    )
    asyncio.run(
        prepare_news_classifiers_experiment(
            experiment_type="news-filtering",
            run_type=VectorNames.TITLE_SUMMARY,
            collection_name="ClassificationEvaluation",
        )
    )
    asyncio.run(
        prepare_news_classifiers_experiment(
            experiment_type="news-filtering",
            run_type=VectorNames.TITLE_CONTENT,
            collection_name="ClassificationEvaluation",
        )
    )
