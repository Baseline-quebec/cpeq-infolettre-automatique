"""App configuration."""

from enum import Enum
from typing import ClassVar, Literal

from decouple import config
from pydantic import BaseModel


class VectorNames(Enum):
    """Vector Names Enum class."""

    TITLE_SUMMARY = "title_summary"
    TITLE_CONTENT = "title_content"


ClassificationAlgos = Literal[
    "MaxMeanScoresNewsClassifier",
    "MaxScoreNewsClassifier",
    "MaxPoolingNewsClassifier",
    "KnNewsClassifier",
    "RandomForestNewsClassifier",
]


class Relevance(Enum):
    """Revelant Enum class."""

    PERTINENT = "Pertinent"
    AUTRE = "Autre"  # Should match Rubric.AUTRE values


class Rubric(Enum):
    """Rubric Enum class."""

    AUTRE = "Autre"  # Should match Relevance.AUTRE values
    CHANGEMENT_CLIMATIQUE_ET_ENERGIE = "Changements climatiques et énergie"
    ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE = (
        "Acceptabilité sociale, bruit et troubles de voisinage"
    )
    AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME = "Aménagement du territoire et urbanisme"
    APPLICATION_DE_LA_LOI_ET_AFFAIRES_JURIDIQUES = "Application de la loi et affaires juridiques"
    BIODIVERSITE_MILIEUX_HUMIDES_ET_ESPECES_EN_PERIL = (
        "Biodiversité, milieux humides et espèces en péril"
    )
    DEVELOPPEMENT_DURABLE_RSE_ET_CRITERES_ESG = "Développement durable, RSE et critères ESG"
    DEVELOPPEMENT_NORDIQUE = "Développement nordique"
    DOMAINE_AEROSPATIAL = "Domaine aérospatial"
    DOMAINE_AGRICOLE = "Domaine agricole"
    EAU_ET_DOMAINE_MARITIME = "Eau et domaine maritime"
    EVALUATIONS_ENVIRONNEMENTALES = "Évaluations environnementales"
    MATIERES_DANGEREUSES_ET_PESTICIDES = "Matières dangereuses et pesticides"
    MATIERES_ORGANIQUES_MATIERES_RESIDUELLES_ECOLOGIE_INDUSTRIELLE_ET_ECONOMIE_CIRCULAIRE = (
        "Matières organiques, matières résiduelles, Écologie industrielle et économie circulaire"
    )
    NOUVELLES_ADMINISTRATIVES = "Nouvelles administratives"
    PECHERIES = "Pêcheries"
    POLITIQUES_PUBLIQUES_ET_GOUVERNEMENTALES = "Politiques publiques et gouvernementales"
    QUALITE_DE_LAIR = "Qualité de l'air"
    RESSOURCES_NATURELLES = "Ressources naturelles"
    SECTEUR_MANUFACTURIER_ET_PME = "Secteur manufacturier et PME"
    SOLS_ET_TERRAINS_CONTAMINES = "Sols et terrains contaminés"
    SUBSTANCES_CHIMIQUES = "Substances chimiques"
    TECHNOLOGIES_PROPRES = "Technologies propres"
    TRANSPORT_ET_MOBILITE_DURABLE = "Transport et mobilité durable"


class OneDriveConfig(BaseModel):
    """Configuration for the OneDrive client."""

    client_id: ClassVar[str] = config("ONEDRIVE_CLIENT_ID", cast=str)
    client_secret: ClassVar[str] = config("ONEDRIVE_CLIENT_SECRET", cast=str)
    tenant_id: ClassVar[str] = config("ONEDRIVE_TENANT_ID", cast=str)
    drive_id: ClassVar[str] = config("ONEDRIVE_DRIVE_ID", cast=str)
    site_url: ClassVar[str] = config("ONEDRIVE_SITE_URL", cast=str)
    folder_name: ClassVar[str] = config("ONEDRIVE_FOLDER_NAME", cast=str)


class EmbeddingModelConfig(BaseModel):
    """Embedding Model dataclass.

    Notes:
    embedding models and info for OpenAI can be found at https://platform.openai.com/docs/guides/embeddings
    """

    embedding_model_id: Literal[
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large",
    ] = "text-embedding-3-large"
    token_encoding: Literal["cl100k_base", "p50k_base", "r50k_base", "gpt2"] = "cl100k_base"
    max_tokens: Literal[8192] = 8192


class VectorstoreConfig(BaseModel):
    """Configuration for the vector store client."""

    collection_name: str = config(
        "WEAVIATE_COLLECTION_NAME",
        "",
        cast=str,
    )

    title_summary_vector_name: VectorNames = VectorNames.TITLE_SUMMARY
    title_content_vector_name: VectorNames = VectorNames.TITLE_CONTENT
    max_nb_items_retrieved: int = config("MAX_NB_ITEM_RETRIEVED", 1000, cast=int)
    hybrid_weight: float = config("VECTORSTORE_HYBRID_WEIGHT", 0.75, cast=float)
    batch_size: int = max(config("BATCH_SIZE", 5, cast=int), 1)
    concurrent_requests: int = max(config("CONCURRENT_REQUESTS", 2, cast=int), 1)
    minimal_score: float = config("VECTORSTORE_MINIMUM_SCORE", 0.0, cast=float)


class CompletionModelConfig(BaseModel):
    """Configuration for the completion model."""

    model: Literal["gpt-4o", "gpt-4-turbo"] = config("COMPLETION_MODEL_ID", "gpt-4o", cast=str)
    temperature: float = config("COMPLETION_MODEL_TEMPERATURE", 0.1, cast=float)


class NewsRelevancyClassifierConfig(BaseModel):
    """Configuration for the news relevancy classifier."""

    classification_model_name: ClassificationAlgos = config(
        "NEWS_RELEVANCY_CLASSIFIER_MODEL_NAME", "MaxPoolingNewsClassifier", cast=str
    )
    vector_name: VectorNames = config(
        "NEWS_RELEVANCY_CLASSIFIER_VECTOR_NAME", "title_content", cast=VectorNames
    )
    threshold: float = config("NEWS_RELEVANCY_CLASSIFIER_THRESHOLD", 0.50, cast=float)


class NewsRubricClassifierConfig(BaseModel):
    """Configuration for the rubric classifier."""

    classification_model_name: ClassificationAlgos = config(
        "NEWS_RUBRIC_CLASSIFIER_MODEL_NAME", "MaxPoolingNewsClassifier", cast=str
    )
    vector_name: VectorNames = config(
        "NEWS_RUBRIC_CLASSIFIER_VECTOR_NAME", "title_summary", cast=VectorNames
    )


class SummaryGeneratorConfig(BaseModel):
    """Configuration for the summary generator."""

    vector_name: VectorNames = config(
        "SUMMARY_GENERATOR_VECTOR_NAME", "title_content", cast=VectorNames
    )
