import google.generativeai as genai
from google.generativeai.embedding import EmbeddingTaskType
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from ...core.base import ProviderBase, ProviderConfigBase


class GeminiConfig(ProviderConfigBase):
    """Gemini-specific configuration with explicit environment binding"""

    embedding_model_name: str = "text-embedding-004"
    model_prefix: str = "models/"

    class Config(ProviderConfigBase.Config):
        env_prefix = "GEMINI_"
        env_file = ".env"
        extra = "ignore"


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
        genai.configure(api_key=config.api_key)  # type: ignore

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


gemini = GeminiLLM()
