from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import google.generativeai as genai  # type: ignore
import vertexai  # type: ignore
import vertexai.generative_models  # type: ignore
from google.generativeai.embedding import EmbeddingTaskType
from pydantic import model_validator
from pydantic_ai.models import KnownModelName, Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers import Provider
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.google_vertex import GoogleVertexProvider
from pydantic_settings import BaseSettings
from sqlmodel import Field
from vertexai.language_models import (  # type: ignore
    TextEmbeddingInput,
    TextEmbeddingModel,
)
from vertexai.language_models._language_models import TextEmbedding  # type: ignore

from src.shared.base import MissingCredentialsError
from src.shared.logging import logger

"""
ENUMS
"""


class SupportedModels(Enum):
    VERTEX = "vertex"
    GEMINI = "gemini"


"""
MODEL CONFIGS
"""


class ProviderConfigBase(BaseSettings):
    """Base class for provider configuration"""

    # Required fields
    model_name: str = Field(..., min_length=1)  # Make required field
    api_key: str = Field(..., min_length=1)  # Required base field

    # Default fields
    default_token_limit: int = Field(default=1024, gt=0)
    default_max_retries: int = Field(default=3, gt=0)
    default_temperature: float = Field(default=1.0, gt=0, lt=1.5)
    default_retries: int = Field(default=2, gt=0)

    class Config:
        extra = "ignore"
        env_file = ".env"

    @model_validator(mode="before")
    def validate_base_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("model_name"):
            raise ValueError("model_name must be provided")
        if not values.get("api_key"):
            raise MissingCredentialsError("api_key must be provided")
        return values


class GoogleModelConfig(ProviderConfigBase):
    """Google model configuration. Helper class for embedding models."""

    embedding_model_name: str = "text-embedding-004"


class GeminiConfig(GoogleModelConfig):
    """Gemini-specific configuration with explicit environment binding"""

    class Config(GoogleModelConfig.Config):
        env_prefix = "GEMINI_"
        env_file = ".env"
        extra = "ignore"


class VertexConfig(GoogleModelConfig):
    """Vertex-specific configuration with explicit environment binding"""

    # extra environment variables
    project_id: str = Field(default="", description="The project ID")
    region: str = Field(default="", description="The region")
    # constants
    dimensionality: int = Field(default=768, ge=1, le=768)

    class Config(GoogleModelConfig.Config):
        env_prefix = "VERTEX_"


"""
LLM PROVIDERS
"""


class ProviderBase(ABC):
    """Abstract base class for all provider implementations"""

    @property
    @abstractmethod
    def provider_name(self) -> KnownModelName:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def provider(self) -> Provider[Any]:
        """Pydantic LLM provider"""
        pass

    @property
    @abstractmethod
    def model(self) -> Model:
        """Pydantic LLM model"""
        pass

    def get_model(self) -> Model:
        return self.model

    def __init__(self, config: ProviderConfigBase):
        self.config = config
        self._validate_credentials()

    def _validate_credentials(self):
        """Validate credentials using Pydantic validation"""
        if not self.config.api_key:
            raise MissingCredentialsError(self.provider_name)
        if not self.config.model_name:
            raise MissingCredentialsError(self.provider_name)

    @abstractmethod
    async def embed_content(
        self, content: str | list[str], task_type: Any | None = None
    ) -> list[float] | list[list[float]]:
        """Embed content using the LLM"""
        pass


class VertexLLM(ProviderBase):
    """Vertex LLM provider"""

    def __init__(self, config: VertexConfig):
        logger.debug("Initializing VertexLLM")
        self.config = config
        super().__init__(self.config)

        self.embedding_model = TextEmbeddingModel.from_pretrained(
            self.config.embedding_model_name
        )
        vertexai.init(project=self.config.project_id, location=self.config.region)

    @property
    def provider(self) -> Provider[Any]:
        return GoogleVertexProvider(project_id=self.config.project_id)

    @property
    def provider_name(self) -> KnownModelName:
        return "google-vertex:gemini-2.0-flash"

    @property
    def model(self) -> Model:
        return GeminiModel("gemini-2.0-flash", provider=self.provider)

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
        task_type: str | None = None,
    ) -> list[float] | list[list[float]]:
        try:
            assert content
            assert isinstance(content, list)
            assert len(content) > 0
            assert all(isinstance(item, str) for item in content)
            assert task_type is not None
        except AssertionError as e:
            raise ValueError("Invalid content or dimensionality") from e

        inputs: list[TextEmbeddingInput | str] = [
            TextEmbeddingInput(text, task_type) for text in content
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


class GeminiLLM(ProviderBase):
    """Gemini LLM provider"""

    def __init__(self, config: GeminiConfig):
        self.config = config
        super().__init__(config)

        self.embedding_model = f"models/{config.embedding_model_name}"
        genai.configure(api_key=config.api_key)  # type: ignore

    @property
    def provider(self) -> Provider[Any]:
        return GoogleGLAProvider(api_key=self.config.api_key)

    @property
    def model(self) -> Model:
        return GeminiModel(model_name=self.config.model_name, provider=self.provider)

    async def embed_content(
        self, content: str | list[str], task_type: EmbeddingTaskType | str | None = None
    ) -> list[float] | list[list[float]]:
        if task_type is not None and isinstance(task_type, str):
            try:
                task_type = EmbeddingTaskType(task_type)
            except ValueError as e:
                raise ValueError(f"Invalid task type: {task_type}") from e

        response = genai.embed_content(  # type: ignore
            model=self.embedding_model,
            content=content,
            task_type=task_type,
        )
        return response["embedding"]

    @property
    def provider_name(self) -> KnownModelName:
        return "google-gla:gemini-2.0-flash"
