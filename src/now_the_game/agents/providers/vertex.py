from enum import Enum

import vertexai
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel

from ...core.base import ProviderBase, ProviderConfigBase


class VertexConfig(ProviderConfigBase):
    """Vertex-specific configuration with explicit environment binding"""

    embedding_model_name: str
    project_id: str
    region: str

    class Config(ProviderConfigBase.Config):
        env_prefix = "VERTEX_"


class VertexEmbeddingTaskType(Enum):
    RETRIEVAL_QUERY = "RETRIEVAL_QUERY"
    RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    CLASSIFICATION = "CLASSIFICATION"
    CLUSTERING = "CLUSTERING"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    FACT_VERIFICATION = "FACT_VERIFICATION"
    CODE_RETRIEVAL_QUERY = "CODE_RETRIEVAL_QUERY"


class VertexLLM(ProviderBase):
    def __init__(self):
        config = VertexConfig()
        super().__init__(config)

        self.provider = GoogleVertexProvider(
            project_id=config.project_id, location=config.region
        )
        self.model = GeminiModel("gemini-2.0-flash", provider=self.provider)
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            config.embedding_model_name
        )
        vertexai.init(project=config.project_id, location=config.region)

    def embed_content(
        self,
        content: list[str],
        task_type: VertexEmbeddingTaskType | str = VertexEmbeddingTaskType.CLUSTERING,
        dimensionality: int = 768,
    ) -> list[float]:
        if dimensionality <= 0 or dimensionality > 768:
            raise ValueError("Choose an output dimensionality between 1 and 768")
        if not isinstance(content, list):
            raise ValueError("Invalid content: must be a list of strings")

        if task_type is not None and isinstance(task_type, str):
            try:
                task_type = VertexEmbeddingTaskType(task_type)
            except ValueError as e:
                raise ValueError(f"Invalid task type: {task_type}") from e

        inputs = [TextEmbeddingInput(text, task_type.value) for text in content]
        kwargs = {"output_dimensionality": dimensionality} if dimensionality else {}

        embeddings = self.embedding_model.get_embeddings(inputs, **kwargs)

        return [embedding.values for embedding in embeddings]
