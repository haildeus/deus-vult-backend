from abc import ABC, abstractmethod
from datetime import datetime
from random import randint
from typing import Any, Generic, TypeVar, overload

from pydantic import ValidationError, model_validator
from pydantic_settings import BaseSettings
from pydantic_ai.models import KnownModelName
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, col, exists, select

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


class EntityNotFoundError(Exception):
    """Raised when an entity is not found"""

    def __init__(self, entity_id: int):
        super().__init__(f"Entity with ID {entity_id} not found")
        self.entity_id = entity_id


class OverloadParametersError(Exception):
    """Raised when the number of provided parameters is >= 1"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BaseSchema(SQLModel):
    object_id: int = Field(
        primary_key=True, default_factory=lambda: randint(1, 1000000)
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BaseModel(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    @overload
    async def add(self, session: AsyncSession, entity: T) -> list[T]: ...

    @overload
    async def add(self, session: AsyncSession, entity: list[T]) -> list[T]: ...

    async def add(self, session: AsyncSession, entity: T | list[T]) -> list[T]:
        """
        Adds an entity to the session. Needs to be flushed.
        Great for adding dependent entities.

        Args:
            session: The session to add the entity to.
            entity: The entity to add.

        Returns:
            The added entity.
        """
        try:
            assert entity
        except AssertionError as e:
            logger.error(f"Error adding entity: {e}")
            raise ValueError("Invalid entity") from e

        if isinstance(entity, list):
            return await self.add_many(session, entity)
        else:
            return await self.add_one(session, entity)

    async def add_one(self, session: AsyncSession, entity: T) -> list[T]:
        """Adds an entity to the session. Needs to be flushed."""
        try:
            checked_entity = await self.pass_insert_checks(session, entity)
        except Exception as e:
            logger.error(f"Error adding entity to session: {e}")
            raise e

        session.add(checked_entity)
        return [checked_entity]

    async def add_many(self, session: AsyncSession, entities: list[T]) -> list[T]:
        """Adds a list of entities to the session. Needs to be flushed."""
        try:
            checked_entities = await self.pass_insert_checks(session, entities)
        except Exception as e:
            logger.error(f"Error adding entities to session: {e}")
            raise e

        session.add_all(checked_entities)
        return checked_entities

    async def get_by_id(self, session: AsyncSession, entity_id: int) -> list[T]:
        """Gets an entity by its ID."""
        query = select(self.model_class).where(self.model_class.object_id == entity_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_all(self, session: AsyncSession) -> list[T]:
        """Gets all entities."""
        query = select(self.model_class)
        result = await session.execute(query)
        return list(result.scalars().all())

    @overload
    async def create(self, session: AsyncSession, entity: T) -> list[T]: ...

    @overload
    async def create(self, session: AsyncSession, entity: list[T]) -> list[T]: ...

    async def create(self, session: AsyncSession, entity: T | list[T]) -> list[T]:
        """
        Creates an entity in the database and flushes the session.

        Args:
            session: The session to add the entity to.
            entity: The entity to create.

        Returns:
            The created entity.
        """
        try:
            assert entity
        except AssertionError as e:
            logger.error(f"Error creating entity: {e}")
            raise e

        if isinstance(entity, list):
            response = await self.add_many(session, entity)
            await session.flush()
            await session.refresh(response)
            return response
        else:
            response = await self.add_one(session, entity)
            await session.flush()
            await session.refresh(response)
            return response

    @overload
    async def remove(self, session: AsyncSession, entity: None) -> bool: ...

    @overload
    async def remove(self, session: AsyncSession, entity: T) -> bool: ...

    @overload
    async def remove(self, session: AsyncSession, entity: list[T]) -> bool: ...

    async def remove(self, session: AsyncSession, entity: list[T] | T | None) -> bool:
        """Removes an entity from the session."""
        try:
            assert entity
        except AssertionError as e:
            logger.error(f"Error removing entity: {e}")
            raise ValueError("Invalid entity") from e

        if not entity:
            return await self.__remove_all(session)
        elif isinstance(entity, list):
            return await self.__remove_many(session, entity)
        else:
            return await self.__remove_one(session, entity.object_id)

    async def __remove_one(self, session: AsyncSession, entity_id: int) -> bool:
        """Private method. Removes an entity by its ID."""
        try:
            assert isinstance(entity_id, int)
        except AssertionError as e:
            logger.error(f"Error removing entity: {e}")
            raise ValueError("Invalid entity ID") from e

        statement = select(self.model_class).where(
            self.model_class.object_id == entity_id
        )
        result = await session.execute(statement)
        entity = result.scalars().first()

        try:
            assert entity
        except AssertionError as e:
            logger.error(f"Error removing entity: {e}")
            raise EntityNotFoundError(entity_id) from e

        await session.delete(entity)
        return True

    async def __remove_many(self, session: AsyncSession, entities: list[T]) -> bool:
        """Private method. Removes entities by their IDs."""
        try:
            assert entities
            assert all(isinstance(entity.object_id, int) for entity in entities)
        except AssertionError as e:
            logger.error(f"Error removing entities: {e}")
            raise ValueError("All entity IDs must be integers") from e

        entity_ids = [entity.object_id for entity in entities]
        statement = select(self.model_class).where(
            col(self.model_class.object_id).in_(entity_ids)
        )
        result = await session.execute(statement)
        entities = list(result.scalars().all())

        try:
            assert entities
            assert all(isinstance(entity.object_id, int) for entity in entities)
        except AssertionError as e:
            logger.error(f"Error removing entities: {e}")
            raise ValueError("All entity IDs must be integers") from e

        for entity in entities:
            await session.delete(entity)
        return True

    async def __remove_all(self, session: AsyncSession) -> bool:
        """Private method. Removes all entities."""
        statement = delete(self.model_class)
        await session.execute(statement)

        try:
            assert await self.__table_is_empty(session)
        except AssertionError as e:
            logger.error(f"Error removing all entities: {e}")
            raise e

        return True

    async def is_present(self, session: AsyncSession, entity_id: int) -> bool:
        """Checks if an entity exists by its ID."""
        query = select(self.model_class).where(self.model_class.object_id == entity_id)
        result = await session.execute(query)
        return result.scalars().first() is not None

    @overload
    async def put(
        self, session: AsyncSession, entity_id: int, new_entity: T
    ) -> bool: ...

    @overload
    async def put(
        self, session: AsyncSession, entity_id: list[int], new_entity: T
    ) -> bool: ...

    async def put(
        self, session: AsyncSession, entity_id: int | list[int], new_entity: T
    ) -> bool:
        """Updates an entity by its ID."""
        if isinstance(entity_id, list):
            return await self.__put_many(session, entity_id, new_entity)
        else:
            return await self.__put_one(session, entity_id, new_entity)

    async def __put_many(
        self, session: AsyncSession, entity_ids: list[int], new_entity: T
    ) -> bool:
        """Updates a list of entities."""
        statement = select(self.model_class).where(
            col(self.model_class.object_id).in_(entity_ids)
        )
        result = await session.execute(statement)
        old_entities = list(result.scalars().all())

        try:
            assert old_entities
            assert all(isinstance(entity.object_id, int) for entity in old_entities)
        except AssertionError as e:
            logger.error(f"Error updating entities: {e}")
            raise ValueError("All entity IDs must be integers") from e

        for old_entity in old_entities:
            new_entity_data = new_entity.model_dump(
                exclude_unset=True, exclude_none=True
            )
            for key, value in new_entity_data.items():
                setattr(old_entity, key, value)
        session.add_all(old_entities)
        return True

    async def count(self, session: AsyncSession) -> int:
        """Counts the number of entities in the table."""
        return await self.__rows(session)

    async def __put_one(
        self, session: AsyncSession, entity_id: int, new_entity: T
    ) -> bool:
        """Updates an entity by its ID."""
        try:
            assert new_entity
            assert entity_id
            assert isinstance(entity_id, int)
        except AssertionError as e:
            logger.error(f"Error updating entity: {e}")
            raise ValueError("Invalid entity") from e

        statement = select(self.model_class).where(
            self.model_class.object_id == entity_id
        )
        result = await session.execute(statement)
        entity = result.scalar_one_or_none()

        try:
            assert entity
            assert isinstance(entity, self.model_class)
        except AssertionError as e:
            raise EntityNotFoundError(entity_id) from e

        new_entity_data = new_entity.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in new_entity_data.items():
            setattr(entity, key, value)
        session.add(entity)
        return True

    @overload
    async def pass_insert_checks(self, session: AsyncSession, entity: T) -> T: ...

    @overload
    async def pass_insert_checks(
        self, session: AsyncSession, entity: list[T]
    ) -> list[T]: ...

    async def pass_insert_checks(
        self, session: AsyncSession, entity: T | list[T]
    ) -> T | list[T]:
        """Private method. Checks if entities are exists in db and validates them."""
        if isinstance(entity, list):
            return await self.__insert_check_for_many(session, entity)
        else:
            return await self.__insert_check_for_one(session, entity)

    async def __insert_check_for_many(
        self, session: AsyncSession, entities: list[T]
    ) -> list[T]:
        """Private method. Checks if entities are exists in db and validates them."""
        checked_entities: list[T] = []

        for entity in entities:
            try:
                entity = await self.__insert_check_for_one(session, entity)
            except Exception as e:
                logger.error(f"Error adding entity: {e}")
                raise e
            checked_entities.append(entity)

        return checked_entities

    async def __insert_check_for_one(self, session: AsyncSession, entity: T) -> T:
        """Private method. Checks if entity is exists in db and"""
        try:
            assert not await self.is_present(session, entity.object_id)
            entity = self.model_class.model_validate(entity)
        except AssertionError as e:
            logger.error(f"Error adding entity: {e}")
            raise EntityAlreadyExistsError(entity.__name__) from e
        except ValidationError as e:
            logger.error(f"Error adding entity: {e}")
            raise ValueError(f"Invalid entity: {e}") from e
        except Exception as e:
            logger.error(f"Error adding entity: {e}")
            raise e

        return entity

    async def __table_is_empty(self, session: AsyncSession) -> bool:
        """Private method. Checks if table is empty."""
        query = select(exists(select(self.model_class)))
        result = await session.execute(query)
        return result.scalar_one_or_none() is None

    async def __rows(self, session: AsyncSession) -> int:
        """Private method. Returns the number of rows in the table."""
        query = select(func.count()).select_from(self.model_class)
        result = await session.execute(query)
        response = result.scalar_one_or_none()
        try:
            assert response
            assert isinstance(response, int)
            assert response > 0

            return response
        except AssertionError as e:
            logger.error(f"Error getting rows: {e}")
            return 0


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
