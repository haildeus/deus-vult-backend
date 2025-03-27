from abc import ABC, abstractmethod
from typing import Any

from pydantic import model_validator
from pydantic_ai.models import KnownModelName
from pydantic_settings import BaseSettings
from sqlmodel import Field

from src.shared.base import MissingCredentialsError


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


class ProviderBase(ABC):
    """Abstract base class for all provider implementations"""

    @property
    @abstractmethod
    def provider_name(self) -> KnownModelName:
        """Provider name"""
        pass

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
