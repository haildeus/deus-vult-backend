from abc import ABC, abstractmethod
from datetime import datetime
from random import randint
from typing import Any, Generic, TypeVar

from pydantic import ValidationError, model_validator
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select

from .. import logger

T = TypeVar("T", bound="BaseSchema")


class MissingCredentialsError(Exception):
    """Raised when required credentials are missing"""

    def __init__(self, provider: str):
        super().__init__(f"Missing credentials for {provider}")
        self.provider = provider


class EntityAlreadyExistsError(Exception):
    """Raised when an entity already exists"""

    def __init__(self, entity: str):
        super().__init__(f"Entity {entity} already exists")
        self.entity = entity


class BaseSchema(SQLModel):
    object_id: int = Field(
        primary_key=True, default_factory=lambda: randint(1, 1000000)
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BaseModel(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    async def add(self, session: AsyncSession, entity: T) -> T:
        """Adds an entity to the session. Needs to be flushed."""
        try:
            entity = await self.__insert_checks(session, entity)
        except Exception as e:
            logger.error(f"Error adding entity to session: {e}")
            raise e

        session.add(entity)
        return entity

    async def create(self, session: AsyncSession, entity: T) -> T:
        """Creates an entity in the database and flushes the session."""
        try:
            entity = await self.__insert_checks(session, entity)
        except Exception as e:
            logger.error(f"Error creating entity: {e}")
            raise e

        session.add(entity)
        await session.flush()
        await session.refresh(entity)
        return entity

    async def get_by_id(self, session: AsyncSession, entity_id: int) -> T | None:
        """Gets an entity by its ID."""
        query = select(self.model_class).where(self.model_class.object_id == entity_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def list(
        self, session: AsyncSession, offset: int = 0, limit: int = 100
    ) -> list[T]:
        """Gets a list of entities."""
        query = select(self.model_class).offset(offset).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def is_present(self, session: AsyncSession, entity_id: int) -> bool:
        """Checks if an entity exists by its ID."""
        query = select(self.model_class).where(self.model_class.object_id == entity_id)
        result = await session.execute(query)
        return result.scalars().first() is not None

    async def __insert_checks(self, session: AsyncSession, entity: T) -> T:
        """Private method. Checks if entity is exists in db and"""
        try:
            assert not await self.is_present(session, entity.object_id)
            entity = self.model_class.model_validate(entity)
        except AssertionError as e:
            raise EntityAlreadyExistsError(entity.__name__) from e
        except ValidationError as e:
            raise ValueError(f"Invalid entity: {e}") from e
        except Exception as e:
            raise ValueError(f"Invalid entity: {e}") from e

        return entity


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
    def provider_name(self) -> str:
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
    def embed_content(self, content: str) -> list[float]:
        """Embed content using the LLM"""
        pass
