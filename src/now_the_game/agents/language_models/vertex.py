from enum import Enum
from typing import Any

import vertexai
import vertexai.generative_models
from pydantic import Field
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from vertexai.language_models._language_models import TextEmbedding

from ...core.base import ProviderBase, ProviderConfigBase


class VertexConfig(ProviderConfigBase):
    """Vertex-specific configuration with explicit environment binding"""

    embedding_model_name: str = "text-embedding-004"
    project_id: str = Field(default="", description="The project ID")
    region: str = Field(default="", description="The region")
    dimensionality: int = Field(default=768, ge=1, le=768)

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
        self.config = VertexConfig()
        super().__init__(self.config)

        self.provider = GoogleVertexProvider(project_id=self.config.project_id)
        self.model = GeminiModel("gemini-2.0-flash", provider=self.provider)
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            self.config.embedding_model_name
        )
        vertexai.init(project=self.config.project_id, location=self.config.region)

    @property
    def provider_name(self) -> KnownModelName:
        return "google-vertex:gemini-2.0-flash"

    async def generate_multimodal(self, prompt: str, image: bytes):
        client = vertexai.generative_models.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        part_1_bytes = vertexai.generative_models.Image.from_bytes(image)
        part_1 = vertexai.generative_models.Part.from_image(part_1_bytes)
        part_2 = vertexai.generative_models.Part.from_text(prompt)

        content = vertexai.generative_models.Content(
            role="user",
            parts=[part_1, part_2],
        )

        response = client.generate_content(
            contents=[content],
        )
        return response

    async def generate_text(self, prompt: str):
        client = vertexai.generative_models.GenerativeModel(
            model_name="gemini-2.0-flash",
        )
        response = client.generate_content(
            contents=[
                vertexai.generative_models.Content(
                    role="user",
                    parts=[vertexai.generative_models.Part.from_text(prompt)],
                )
            ],
        )
        return response

    async def embed_content(
        self,
        content: str | list[str],
        task_type: VertexEmbeddingTaskType | str | None = None,
    ) -> list[float] | list[list[float]]:
        try:
            assert content
            assert isinstance(content, list)
            assert len(content) > 0
            assert all(isinstance(item, str) for item in content)
            assert task_type is not None and isinstance(
                task_type, VertexEmbeddingTaskType
            )
        except AssertionError as e:
            raise ValueError("Invalid content or dimensionality") from e

        inputs: list[TextEmbeddingInput | str] = [
            TextEmbeddingInput(text, task_type.value) for text in content
        ]

        embeddings = self.embedding_model.get_embeddings(
            texts=inputs, output_dimensionality=self.config.dimensionality
        )
        try:
            assert embeddings
            assert len(embeddings) > 0
            assert isinstance(embeddings[0], TextEmbedding)
            assert embeddings[0].values
        except AssertionError as e:
            raise ValueError("Invalid embeddings") from e

        return_array: list[list[float]] = []
        for embedding in embeddings:
            return_array.append(embedding.values)

        if len(return_array) == 1:
            return return_array[0]
        return return_array


vertex = VertexLLM()
