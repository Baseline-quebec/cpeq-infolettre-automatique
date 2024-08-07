"""Depencies injection functions for the Service class."""

from collections.abc import Iterator
from typing import Annotated, Any, cast

import httpx
import weaviate
from decouple import config
from fastapi import Depends
from O365.account import Account
from O365.drive import Folder
from openai import AsyncOpenAI

from cpeq_infolettre_automatique.classification_algo import (
    KnNewsClassifier,
    MaxMeanScoresNewsClassifier,
    MaxPoolingNewsClassifier,
    MaxScoreNewsClassifier,
    NewsClassifier,
    RandomForestNewsClassifier,
)
from cpeq_infolettre_automatique.completion_model import (
    CompletionModel,
    OpenAICompletionModel,
)
from cpeq_infolettre_automatique.config import (
    ClassificationAlgos,
    CompletionModelConfig,
    EmbeddingModelConfig,
    NewsRelevancyClassifierConfig,
    NewsRubricClassifierConfig,
    OneDriveConfig,
    SummaryGeneratorConfig,
    VectorNames,
    VectorstoreConfig,
)
from cpeq_infolettre_automatique.embedding_model import (
    EmbeddingModel,
    OpenAIEmbeddingModel,
)
from cpeq_infolettre_automatique.news_classifier import (
    NewsRelevancyClassifier,
    NewsRubricClassifier,
)
from cpeq_infolettre_automatique.news_producer import NewsProducer
from cpeq_infolettre_automatique.repositories import NewsRepository, OneDriveNewsRepository
from cpeq_infolettre_automatique.service import Service
from cpeq_infolettre_automatique.summary_generator import SummaryGenerator
from cpeq_infolettre_automatique.utils import get_or_create_subfolder, prepare_dates
from cpeq_infolettre_automatique.vectorstore import Vectorstore
from cpeq_infolettre_automatique.webscraper_io_client import WebscraperIoClient


class ApiDependency:
    """A base class for FastAPI dependency injection. Any dependency should redefine some or all the methods of this class."""

    @classmethod
    def setup(cls) -> None:
        """Create the global resources of the dependency. Call this method at app startup in `lifespan`."""

    def __init__(self) -> None:
        """Create a new instance of the dependency.

        Will be called by FastAPI when the dependency is injected with Depends(). The instanciated ApiDependency object should define __call__ to return the dependency to inject.

        Any subdependencies used by the dependency should be injected here, in the __init__ method.
        """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Initialize if needed, and then return the dependency to inject. Can act as a factory."""

    @classmethod
    def teardown(cls) -> Any:
        """Clean up the global resources of the dependency. Call this method at app takedown in `lifespan`."""

    def __hash__(self) -> int:
        """Return a hash of the dependency type. Used to get dependency in app.dependency_overrides."""
        return hash(type(self))


class HttpClientDependency(ApiDependency):
    """Dependency class for the Singleton HTTP Client."""

    client: httpx.AsyncClient

    @classmethod
    def setup(cls) -> None:
        """Setup dependency."""
        timeout = httpx.Timeout(timeout=60.0)
        cls.client = httpx.AsyncClient(http2=True, timeout=timeout)

    def __call__(self) -> httpx.AsyncClient:
        """Returns the HTTP Client instance.

        Returns:
            The HTTP Client.
        """
        return self.client

    @classmethod
    async def teardown(cls) -> Any:
        """Free resources held by the class."""
        await cls.client.aclose()


class OneDriveDependency(ApiDependency):
    """Dependency class for the Singleton O365 Account client."""

    news_folder: Folder
    week_folder: Folder

    @classmethod
    def setup(cls) -> None:
        """Setup dependency.

        Raises:
        RuntimeError: If the authentication with Office365 fails.
        RuntimeError: If the requested Sharepoint Site was not found.
        RuntimeError: If the requested OneDrive instance was not found.
        """
        account = Account(
            (OneDriveConfig.client_id, OneDriveConfig.client_secret),
            auth_flow_type="credentials",
            tenant_id=OneDriveConfig.tenant_id,
        )
        if not account.authenticate():
            msg = "Authentication with Office365 failed."
            raise RuntimeError(msg)

        site_url = OneDriveConfig.site_url
        site = account.sharepoint().get_site(site_url)
        if site is None:
            msg = f"The requested Sharepoint Site {site_url} was not found."
            raise RuntimeError(msg)

        drive_id = OneDriveConfig.drive_id
        drive = site.site_storage.get_drive(drive_id)
        if drive is None:
            msg = f"The requested OneDrive instance with id {drive_id} was not found."
            raise RuntimeError

        root_folder: Folder = cast(Folder, drive.get_root_folder())
        news_folder: Folder = get_or_create_subfolder(
            parent_folder=root_folder, folder_name=OneDriveConfig.folder_name
        )
        _, end_date = prepare_dates()
        week_folder: Folder = get_or_create_subfolder(
            parent_folder=news_folder, folder_name=str(end_date.date())
        )

        cls.news_folder = news_folder
        cls.week_folder = week_folder

    def __call__(self) -> tuple[Folder, Folder]:
        """Calls the dependency.

        Returns:
            A tuple container both the news and the week folder.
        """
        return (self.news_folder, self.week_folder)

    @classmethod
    def get_folder_name(cls) -> str:
        """The name of the folder containing the news and the newsletter.

        Returns:
            The folder name.
        """
        return f"{cls.news_folder.name}/{cls.week_folder.name}"


class VectorstoreClientDependency(ApiDependency):
    """Dependency class for the Singleton Vectorstore client."""

    vectorstore_client: weaviate.WeaviateClient

    @classmethod
    def setup(cls) -> None:
        """Setup dependency.

        Raises:
            ConnectionError: If the Vectorstore is not ready.
        """
        cls.vectorstore_client = weaviate.connect_to_embedded(
            version=config("WEAVIATE_VERSION", cast=str),
            persistence_data_path=config("WEAVIATE_PERSISTENCE_DATA_PATH", cast=str),
            port=config("WEAVIATE_HTTP_PORT", cast=int),
            grpc_port=config("WEAVIATE_GRPC_PORT", cast=int),
        )
        if not cls.vectorstore_client.is_ready():
            error_msg = "Vectorstore is not ready"
            raise ConnectionError(error_msg)

    def __call__(self) -> weaviate.WeaviateClient:
        """Calls the dependency.

        Returns:
            The Vectorstore client.
        """
        return self.vectorstore_client

    @classmethod
    def teardown(cls) -> None:
        """Free resources held by the class."""
        cls.vectorstore_client.close()


def get_webscraperio_client(
    http_client: Annotated[httpx.AsyncClient, Depends(HttpClientDependency())],
) -> WebscraperIoClient:
    """Gets a WebscraperIClient instance.

    Returns:
        A configured WebscraperIoClient instance.
    """
    return WebscraperIoClient(http_client=http_client, api_token=config("WEBSCRAPER_IO_API_KEY"))


def get_news_repository(
    folders: Annotated[tuple[Folder, Folder], Depends(OneDriveDependency())],
) -> NewsRepository:
    """Gets a NewsRepository instance.

    Returns:
        A configured NewsRepository instance.
    """
    (_, week_folder) = folders
    return OneDriveNewsRepository(week_folder)


def get_openai_client() -> AsyncOpenAI:
    """Gets the OpenAI client.

    Returns:
        An AsyncOpenAI instance with the provided API key.
    """
    return AsyncOpenAI(api_key=config("OPENAI_API_KEY"), max_retries=4)


def get_embedding_model(
    openai_client: Annotated[AsyncOpenAI, Depends(get_openai_client)],
) -> EmbeddingModel:
    """Gets an EmbeddingModel instance.

    Returns:
        An EmbeddingModel instance with the provided API key.
    """
    embedding_model_config = EmbeddingModelConfig()
    return OpenAIEmbeddingModel(
        client=openai_client, embedding_model_config=embedding_model_config
    )


def get_vectorstore_client() -> Iterator[weaviate.WeaviateClient]:
    """Get the vectorstore client.

    Raises:
        ValueError: If the vectorstore is not ready.
    """
    try:
        client: weaviate.WeaviateClient = weaviate.connect_to_embedded(
            version=config("WEAVIATE_VERSION", cast=str),
            persistence_data_path=config("WEAVIATE_PERSISTENCE_DATA_PATH", cast=str),
            port=config("WEAVIATE_HTTP_PORT", cast=int),
            grpc_port=config("WEAVIATE_GRPC_PORT", cast=int),
        )
        if not client.is_ready():
            error_msg = "Vectorstore is not ready"
            raise ValueError(error_msg)
        yield client
    finally:
        client.close()


def get_vectorstore(
    vectorstore_client: Annotated[weaviate.WeaviateClient, Depends(VectorstoreClientDependency())],
    embedding_model: Annotated[EmbeddingModel, Depends(get_embedding_model)],
) -> Vectorstore:
    """Gets a Vectorstore instance.

    Returns:
        A Vectorstore instance with the provided dependencies.
    """
    vectorstore_config = VectorstoreConfig()
    return Vectorstore(
        vectorstore_client=vectorstore_client,
        embedding_model=embedding_model,
        vectorstore_config=vectorstore_config,
    )


def get_completion_model(
    openai_client: Annotated[AsyncOpenAI, Depends(get_openai_client)],
) -> CompletionModel:
    """Gets a CompletionModel instance.

    Returns:
        A CompletionModel instance.
    """
    completion_model_config = CompletionModelConfig()

    return OpenAICompletionModel(
        client=openai_client,
        completion_model_config=completion_model_config,
    )


def get_summary_generator(
    completion_model: Annotated[CompletionModel, Depends(get_completion_model)],
    vectorstore: Annotated[Vectorstore, Depends(get_vectorstore)],
) -> SummaryGenerator:
    """Gets a SummaryGenerator instance.

    Returns:
        A CompletionModel instance.
    """
    summary_generator_config = SummaryGeneratorConfig()
    return SummaryGenerator(
        completion_model=completion_model,
        vectorstore=vectorstore,
        summary_generator_config=summary_generator_config,
    )


def create_news_classifier(
    vectorstore: Vectorstore,
    vector_name: VectorNames,
    classifier_type: ClassificationAlgos,
    train_data: list[tuple[str, list[float]]] | None = None,
    **kwargs: Any,
) -> NewsClassifier:
    """Create a NewsClassifier based on the classifier_type.

    Args:
        vectorstore: The vectorstore to use for classification.
        vector_name: The name of the vector to use for classification.
        classifier_type: The type of classifier to create.
        train_data: The training data to use for classification.
        **kwargs: The arguments to pass to the classifier.

    Notes:
        Current implementation of news classifiers dependency retrains a new model
        each API Call. It is not scallable nor robust, but as a tradeoff, it offers
        simplicity and works as is, without external dependencies. (I.E. path pointing to weights and biases)

        # TODO(Olivier Belhumeur): This will require more work when deployed to production.

    Returns:
        The NewsClassifier.

    Raises:
        ValueError: If the classifier_type is unknown.
    """
    model: NewsClassifier
    model_dict = {
        "MaxMeanScoresNewsClassifier": MaxMeanScoresNewsClassifier,
        "MaxScoreNewsClassifier": MaxScoreNewsClassifier,
        "MaxPoolingNewsClassifier": MaxPoolingNewsClassifier,
        "KnNewsClassifier": KnNewsClassifier,
        "RandomForestNewsClassifier": RandomForestNewsClassifier,
    }
    if classifier_type in model_dict:
        model = model_dict[classifier_type](vectorstore, vector_name=vector_name, **kwargs)
    else:
        error_msg = f"Unknown classifier type: {classifier_type}"
        raise ValueError(error_msg)
    model.setup(train_data)
    return model


def get_news_rubric_classifier(
    vectorstore: Annotated[Vectorstore, Depends(get_vectorstore)],
) -> NewsRubricClassifier:
    """Gets a NewsRubricClassifier instance.

    Returns:
        A NewsRubricClassifier instance.
    """
    news_rubric_classifier_config = NewsRubricClassifierConfig()
    news_classifier_model = create_news_classifier(
        vectorstore=vectorstore,
        classifier_type=news_rubric_classifier_config.classification_model_name,
        vector_name=news_rubric_classifier_config.vector_name,
    )
    return NewsRubricClassifier(model=news_classifier_model)


def get_news_relevancy_classifier(
    vectorstore: Annotated[Vectorstore, Depends(get_vectorstore)],
) -> NewsRelevancyClassifier:
    """Gets a NewsRelevancyClassifierConfig instance.

    Returns:
        A NewsRelevancyClassifierConfig instance.
    """
    news_relevancy_classifier_config = NewsRelevancyClassifierConfig()
    news_classifier_model = create_news_classifier(
        vectorstore=vectorstore,
        classifier_type=news_relevancy_classifier_config.classification_model_name,
        vector_name=news_relevancy_classifier_config.vector_name,
    )
    return NewsRelevancyClassifier(
        model=news_classifier_model,
        news_relevancy_classifier_config=news_relevancy_classifier_config,
    )


def get_news_producer(
    summary_generator: Annotated[SummaryGenerator, Depends(get_summary_generator)],
    news_rubric_classifier: Annotated[NewsRubricClassifier, Depends(get_news_rubric_classifier)],
) -> NewsProducer:
    """Gets a NewsProducer instance.

    Returns:
        A NewsProducer instance.
    """
    return NewsProducer(
        summary_generator=summary_generator,
        news_rubric_classifier=news_rubric_classifier,
    )


def get_service(
    webscraper_io_client: Annotated[WebscraperIoClient, Depends(get_webscraperio_client)],
    news_repository: Annotated[NewsRepository, Depends(get_news_repository)],
    news_relevancy_classifier: Annotated[
        NewsRelevancyClassifier, Depends(get_news_relevancy_classifier)
    ],
    news_producer: Annotated[NewsProducer, Depends(get_news_producer)],
) -> Service:
    """Gets the Service instance.

    Returns:
        A Service instance with the provided dependencies.
    """
    start_date, end_date = prepare_dates()
    return Service(
        start_date=start_date,
        end_date=end_date,
        webscraper_io_client=webscraper_io_client,
        news_repository=news_repository,
        news_relevancy_classifier=news_relevancy_classifier,
        news_producer=news_producer,
    )
