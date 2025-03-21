from abc import ABC, abstractmethod
from random import randint
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import model_validator
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select

T = TypeVar("T", bound=SQLModel)


class MissingCredentialsError(Exception):
    """Raised when required credentials are missing"""

    def __init__(self, provider: str):
        super().__init__(f"Missing credentials for {provider}")
        self.provider = provider


class BaseSchema(SQLModel):
    object_id: int = Field(
        primary_key=True, default_factory=lambda: randint(1, 1000000)
    )


class BaseModel(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    async def create(self, session: AsyncSession, entity: T) -> T:
        entity = self.model_class.model_validate(entity)
        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return entity

    async def get_by_id(self, session: AsyncSession, entity_id: UUID | int) -> T | None:
        query = select(self.model_class).where(
            self.model_class.character_id == entity_id
        )
        result = await session.exec(query)
        return result.first()

    async def list(
        self, session: AsyncSession, offset: int = 0, limit: int = 100
    ) -> list[T]:
        query = select(self.model_class).offset(offset).limit(limit)
        result = await session.exec(query)
        return result.scalars().all()

    async def is_present(self, session: AsyncSession, entity_id: UUID | int) -> bool:
        query = select(self.model_class).where(
            self.model_class.character_id == entity_id
        )
        result = await session.exec(query)
        return result.first() is not None


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
    def validate_base_fields(cls, values):
        if not values.get("model_name"):
            raise ValueError("model_name must be provided")
        if not values.get("api_key"):
            raise MissingCredentialsError("api_key must be provided")


class ProviderBase(ABC):
    """Abstract base class for all provider implementations"""

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
    def embed_content(self, content: str) -> list[float]:
        """Embed content using the LLM"""
        pass
