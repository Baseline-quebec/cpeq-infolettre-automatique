"""Implementation of the Classification Evaluation Module."""

import json
import operator
import tempfile
from collections.abc import Iterator
from pathlib import Path

import mlflow
from beir.retrieval.evaluation import EvaluateRetrieval
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    classification_report,
    log_loss,
)
from tqdm import tqdm

from cpeq_infolettre_automatique.config import Relevance, Rubric, VectorstoreConfig
from cpeq_infolettre_automatique.dependencies import (
    get_embedding_model,
    get_openai_client,
    get_vectorstore_client,
)
from cpeq_infolettre_automatique.news_classifier import (
    KnNewsClassifier,
    MaxMeanScoresNewsClassifier,
    MaxPoolingNewsClassifier,
    MaxScoreNewsClassifier,
    NewsClassifier,
    NewsFilterer,
    RandomForestNewsClassifier,
    RubricClassifier,
)
from cpeq_infolettre_automatique.schemas import News
from cpeq_infolettre_automatique.vectorstore import Vectorstore


class ClassificationEvaluation:
    """Classification Evaluation Module."""

    def __init__(
        self,
        q_rels: dict[str, dict[str, int]],
        results: dict[str, dict[str, float]],
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
            results_values[q_id] = {label: score for label, score in scores.items()}
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
                y_score_items.append((key, value))
            y_score_items.sort(key=operator.itemgetter(1), reverse=True)
            y_scores_new.append(y_score_items)
        return y_scores_new

    def classification_report(self) -> dict[str, float | dict[str, float]]:
        """Classification Report."""
        report: dict[str, float | dict[str, float]] = classification_report(
            self.y_true, self.y_pred, output_dict=True
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
) -> Iterator[tuple[list[tuple[News, str, list[float]]], tuple[News, str, list[float]]]]:
    """Get Dataset."""
    news_vectors = vectorstore.read_many_with_vectors()
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
) -> Iterator[tuple[list[tuple[News, str, list[float]]], tuple[News, str, list[float]]]]:
    """Get Dataset."""
    news_vectors = vectorstore.read_many_with_vectors()
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


async def run_rubric_classifiers_experiment(
    experiment_name: str,
    run_name: str,
    rubric_classifiers: list[RubricClassifier],
    vectorstore: Vectorstore,
) -> None:
    """Run Experiment."""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    target_names = [rubric.value for rubric in Rubric]
    parent_run = mlflow.search_runs(
        experiment_ids=[experiment_id], filter_string=f"run_name='{run_name}'"
    )
    parent_run_id = None
    if not parent_run.empty:
        parent_run_id = parent_run["run_id"][0]
    with mlflow.start_run(
        run_id=parent_run_id, run_name=run_name, experiment_id=experiment_id
    ) as parent_run:
        for rubric_classifier in tqdm(rubric_classifiers):
            model_name = rubric_classifier.model_name
            child_run_name = f"{run_name}-{model_name}"
            child_run = mlflow.search_runs(
                experiment_ids=[experiment_id], filter_string=f"run_name='{child_run_name}'"
            )
            child_run_id = None
            if not child_run.empty:
                child_run_id = child_run["run_id"][0]
            with mlflow.start_run(
                run_id=child_run_id,
                run_name=child_run_name,
                experiment_id=experiment_id,
                nested=True,
            ) as child_run:
                q_rels = {}
                results = {}
                for i, dataset in tqdm(
                    enumerate(leave_one_out_rubric_classification_dataset_generator(vectorstore))
                ):
                    train_news_class_vector, test_news_class_vector = dataset
                    test_news, test_class, test_embedding = test_news_class_vector
                    ids_to_keep = [
                        Vectorstore.create_uuid(news) for news, _, _ in train_news_class_vector
                    ]
                    train_class_vector = [
                        (class_, embedding) for _, class_, embedding in train_news_class_vector
                    ]
                    rubric_classifier.news_classifier.setup(train_class_vector)
                    q_rels[str(i)] = {test_class: 1}
                    pred = await rubric_classifier.news_classifier.predict_probs(
                        news=test_news, embedding=test_embedding, ids_to_keep=ids_to_keep
                    )
                    results[str(i)] = pred

                run_classification_evaluation(q_rels, results, target_names)
                mlflow.log_params(rubric_classifier.model_info)
                mlflow.log_param("fields", run_name)


async def run_news_filterers_experiment(
    experiment_name: str,
    run_name: str,
    news_filterers: list[NewsFilterer],
    vectorstore: Vectorstore,
) -> None:
    """Run Experiment."""
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    target_names = [relevance.value for relevance in Relevance]
    target_names.sort()
    parent_run = mlflow.search_runs(
        experiment_ids=[experiment_id], filter_string=f"run_name='{run_name}'"
    )
    parent_run_id = None
    if not parent_run.empty:
        parent_run_id = parent_run["run_id"][0]
    with mlflow.start_run(
        run_id=parent_run_id, run_name=run_name, experiment_id=experiment_id
    ) as parent_run:
        for news_filtrerer in tqdm(news_filterers):
            model_name = news_filtrerer.model_name
            child_run_name = f"{run_name}-{model_name}"
            child_run = mlflow.search_runs(
                experiment_ids=[experiment_id], filter_string=f"run_name='{child_run_name}'"
            )
            child_run_id = None
            if not child_run.empty:
                child_run_id = child_run["run_id"][0]
            with mlflow.start_run(
                run_id=child_run_id,
                run_name=child_run_name,
                experiment_id=experiment_id,
                nested=True,
            ) as child_run:
                q_rels = {}
                results = {}
                for i, dataset in tqdm(
                    enumerate(leave_one_out_news_filtering_dataset_generator(vectorstore))
                ):
                    train_news_class_vector, test_news_class_vector = dataset
                    test_news, test_class, test_embedding = test_news_class_vector
                    ids_to_keep = [
                        Vectorstore.create_uuid(news) for news, _, _ in train_news_class_vector
                    ]
                    train_class_vector = [
                        (class_, embedding) for _, class_, embedding in train_news_class_vector
                    ]
                    news_filtrerer.news_classifier.setup(train_class_vector)
                    q_rels[str(i)] = {test_class: 1}
                    pred = await news_filtrerer.news_classifier.predict_probs(
                        news=test_news, embedding=test_embedding, ids_to_keep=ids_to_keep
                    )
                    results[str(i)] = pred

                run_classification_evaluation(q_rels, results, target_names)
                mlflow.log_params(news_filtrerer.model_info)
                mlflow.log_param("fields", run_name)


def run_classification_evaluation(
    q_rels: dict[str, dict[str, int]],
    results: dict[str, dict[str, float]],
    target_names: list[str],
) -> None:
    """Run Classification Evaluation."""
    classification_evaluation = ClassificationEvaluation(q_rels, results, target_names)
    mlflow.log_metrics(classification_evaluation.classification_metrics())
    retriever_metrics = classification_evaluation.retriever_metrics()
    for metrics in retriever_metrics:
        for key, value in metrics.items():
            new_key = key.split("_")[0]
            k = int(key.split("_")[-1])
            mlflow.log_metric(new_key, value, step=k)
    classification_report = classification_evaluation.classification_report()
    classification_report_txt: str = classification_evaluation.classification_report_txt()  # type: ignore[assignment]
    with tempfile.TemporaryDirectory() as tmp_dir:
        json_path = Path(tmp_dir, "classification_report.json")
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(classification_report, f, indent=2, ensure_ascii=False)
        txt_path = Path(tmp_dir, "classification_report.txt")
        txt_path.write_text(classification_report_txt)

        mlflow.log_artifacts(tmp_dir)

    fig = classification_evaluation.confusion_matrix().figure_

    mlflow.log_figure(fig, "confusion_matrix.png", save_kwargs={"bbox_inches": "tight"})

    fig = classification_evaluation.roc_curve().figure_

    mlflow.log_figure(fig, "roc_curve.png", save_kwargs={"bbox_inches": "tight"})


async def prepare_rubric_classifier_experiment(
    experiment_name: str, run_name: str, collection_name: str
) -> None:
    """Main Function."""
    vectorstore_config = VectorstoreConfig(collection_name=collection_name)

    openai_client = get_openai_client()
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        try:
            vectorstore = Vectorstore(embedding_model, vectorstore_client, vectorstore_config)
            news_classifiers = [
                MaxMeanScoresNewsClassifier(vectorstore),
                KnNewsClassifier(vectorstore),
                MaxScoreNewsClassifier(vectorstore),
                RandomForestNewsClassifier(vectorstore),
                MaxPoolingNewsClassifier(vectorstore),
            ]
            rubric_classifiers = [
                RubricClassifier(news_classifier) for news_classifier in news_classifiers
            ]
            await run_rubric_classifiers_experiment(
                experiment_name, run_name, rubric_classifiers, vectorstore
            )
        finally:
            vectorstore_client.close()


async def prepare_news_filterers_experiment(
    experiment_name: str, run_name: str, collection_name: str
) -> None:
    """Main Function."""
    vectorstore_config = VectorstoreConfig(collection_name=collection_name)

    openai_client = get_openai_client()
    embedding_model = get_embedding_model(openai_client)
    for vectorstore_client in get_vectorstore_client():
        try:
            vectorstore = Vectorstore(embedding_model, vectorstore_client, vectorstore_config)
            news_classifiers = [
                KnNewsClassifier(vectorstore),
                RandomForestNewsClassifier(vectorstore),
                MaxPoolingNewsClassifier(vectorstore),
            ]
            news_filterers = [
                NewsFilterer(news_classifier) for news_classifier in news_classifiers
            ]
            await run_news_filterers_experiment(
                experiment_name, run_name, news_filterers, vectorstore
            )
        finally:
            vectorstore_client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(
        prepare_rubric_classifier_experiment(
            experiment_name="cpeq-rubric-classification",
            run_name="title-summary",
            collection_name="ClassificationEvaluationSummary",
        )
    )
    asyncio.run(
        prepare_rubric_classifier_experiment(
            experiment_name="cpeq-rubric-classification",
            run_name="title-content",
            collection_name="ClassificationEvaluationContent",
        )
    )
    asyncio.run(
        prepare_news_filterers_experiment(
            experiment_name="cpeq-news-filtering",
            run_name="title-summary",
            collection_name="ClassificationEvaluationSummary",
        )
    )
    asyncio.run(
        prepare_news_filterers_experiment(
            experiment_name="cpeq-news-filtering",
            run_name="title-content",
            collection_name="ClassificationEvaluationContent",
        )
    )
