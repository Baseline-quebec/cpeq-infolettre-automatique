"""App configuration."""

from enum import Enum
from pathlib import Path
from typing import ClassVar, Literal

from decouple import config


sitemaps = [
    {"sitemap_id": "some-id"},
]


class Rubric(str, Enum):  # noqa: UP042
    """Rubric Enum class."""

    CHANGEMENT_CLIMATIQUE_ET_ENERGIE = "Changements climatiques et énergie"
    ACCEPTABILITE_SOCIALE_BRUIT_ET_TROUBLES_DE_VOISINAGE = (
        "Acceptabilité sociale, bruit et troubles de voisinage"
    )
    AMENAGEMENT_DU_TERRITOIRE_ET_URBANISME = "Aménagement du territoire et urbanisme"
    APPLICATION_DE_LA_LOI_ET_AFFAIRES_JURIDIQUES = "Application de la loi et affaires juridiques"
    BIODIVERSITE_MILIEUX_HUMIDES_ET_ESPECES_EN_PERIL = (
        "Biodiversité, milieux humides et espèces en péril"
    )
    CARRIERES_ET_SABLIERES = "Carrières et sablières"
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
    MODIFICATIONS_LEGISLATIVES_ET_REGLEMENTAIRES_EN_BREF = (
        "Modifications législatives et réglementaires en bref"
    )


VECTORSTORE_CONTENT_FILEPATH: Path = Path("rubrics", "rubrics.json")


class EmbeddingModelConfig:
    """Embedding Model dataclass.

    Notes:
    embedding models and info for OpenAI can be found at https://platform.openai.com/docs/guides/embeddings
    """

    embedding_model_id: ClassVar[
        Literal[
            "ext-embedding-ada-002",
            "text-embedding-3-small",
            "text-embedding-3-large",
        ]
    ] = "text-embedding-3-large"
    token_encoding: ClassVar[Literal["cl100k_base", "p50k_base", "r50k_base", "gpt2"]] = (
        "cl100k_base"
    )
    max_tokens: ClassVar[int] = 8192


class VectorstoreConfig:
    """Configuration for the vector store client."""

    collection_name: ClassVar[str] = config("WEAVIATE_COLLECTION_NAME", "")


class RetrieverConfig:
    """Retriever Config dataclass."""

    vectorstore_config: ClassVar[VectorstoreConfig] = VectorstoreConfig()
    top_k: ClassVar[int] = int(config("NB_ITEM_RETRIEVED", 5))
    hybrid_weight: ClassVar[float] = 0.75


class WeaviateConfig:
    """Weaviate Config dataclass."""

    query_maximum_results: ClassVar[int] = max(int(config("QUERY_MAXIMUM_RESULTS", 10000)), 1)
    batch_size: ClassVar[int] = max(int(config("BATCH_SIZE", 5)), 1)
    concurrent_requests: ClassVar[int] = max(int(config("CONCURRENT_REQUESTS", 2)), 1)
