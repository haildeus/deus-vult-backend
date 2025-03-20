import google.generativeai as genai
from google.generativeai.embedding import EmbeddingTaskType
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from .base import ProviderBase, ProviderConfig


class GeminiConfig(ProviderConfig):
    """Gemini-specific configuration with explicit environment binding"""

    embedding_model_name: str
    model_prefix: str = "models/"

    class Config(ProviderConfig.Config):
        env_prefix = "GEMINI_"


class GeminiLLM(ProviderBase):
    def __init__(self):
        config = GeminiConfig()
        super().__init__(config)

        self.provider = GoogleGLAProvider(api_key=config.api_key)
        self.model = GeminiModel(
            model_name=config.model_name,
            provider=self.provider,
        )
        self.embedding_model = f"{config.model_prefix}{config.embedding_model_name}"
        genai.configure(api_key=config.api_key)

    def embed_content(
        self, content: str, task_type: EmbeddingTaskType | str | None = None
    ) -> list[float]:
        if task_type is not None and isinstance(task_type, str):
            try:
                task_type = EmbeddingTaskType(task_type)
            except ValueError as e:
                raise ValueError(f"Invalid task type: {task_type}") from e

        response = genai.embed_content(
            model=self.embedding_model,
            content=content,
            task_type=task_type,
        )
        return response["embedding"]
