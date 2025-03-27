from datetime import datetime
from random import randint
from typing import Any, Generic, TypeVar, overload

from pydantic import ValidationError
from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, col, exists, select

from src.shared.database import metadata
from src.shared.logging import logger

T = TypeVar("T", bound="BaseSchema")


class MissingCredentialsError(Exception):
    """Raised when required credentials are missing"""

    def __init__(self, provider: str):
        super().__init__(f"Missing credentials for {provider}")
        self.provider = provider


class EntityAlreadyExistsError(Exception):
    """Raised when an entity already exists"""

    DEFAULT_ENTITY_TYPE = "Entity"

    def __init__(self, entity: str | int, entity_type: str | None = None):
        entity_type = entity_type or self.DEFAULT_ENTITY_TYPE

        if isinstance(entity, int):
            logger.debug(f"{entity_type} object (ID: {entity}) already exists")
            super().__init__(f"{entity_type} object (ID: {entity}) already exists")
        else:
            logger.debug(f"{entity_type} {entity} already exists")
            super().__init__(f"{entity_type} {entity} already exists")
        self.entity = entity


class EntityNotFoundError(Exception):
    """Raised when an entity is not found"""

    def __init__(self, entity_id: str | int):
        if isinstance(entity_id, int):
            logger.debug(f"Entity with ID {entity_id} not found")
            super().__init__(f"Entity with ID {entity_id} not found")
        else:
            logger.debug(f"Entity with ID {entity_id} not found")
            super().__init__(f"Entity with ID {entity_id} not found")
        self.entity_id = entity_id


class OverloadParametersError(Exception):
    """Raised when the number of provided parameters is >= 1"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BaseSchema(SQLModel):
    object_id: int = Field(
        primary_key=True, default_factory=lambda: randint(1, 100000000)
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # We need this to set shared metadata for all models
    metadata = metadata


class BaseModel(Generic[T]):
    def __init__(self, model_class: type[T]):
        self.model_class = model_class

    def __dict_keys(self) -> list[str]:
        return [
            key for key in self.model_class.__dict__.keys() if not key.startswith("_")
        ]

    @overload
    async def add(self, session: AsyncSession, entity: T) -> list[T]: ...

    @overload
    async def add(self, session: AsyncSession, entity: list[T]) -> list[T]: ...

    async def add(self, session: AsyncSession, entity: T | list[T]) -> list[T] | None:
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
            # TODO: Adapt the single-entity logic to the many-entity logic
            return await self.add_many(session, entity)
        else:
            try:
                response = await self.add_one(session, entity)

                object_id = response[0].object_id
                object_name = self.model_class.__name__
                logger.debug(f"Added {object_name} to session: {object_id}")
                return response
            except EntityAlreadyExistsError:
                return
            except Exception as e:
                logger.error(f"Error adding entity: {e}")
                raise e

    async def add_one(self, session: AsyncSession, entity: T) -> list[T]:
        """Adds an entity to the session. Needs to be flushed."""
        try:
            checked_entity = await self.pass_insert_checks(session, entity)
        except EntityAlreadyExistsError as e:
            raise e
        except Exception as e:
            logger.error(f"Error adding entity to session: {e}")
            raise e

        session.add(checked_entity)
        logger.debug(f"Added entity to session: {checked_entity}")
        return [checked_entity]

    async def add_many(self, session: AsyncSession, entities: list[T]) -> list[T]:
        """Adds a list of entities to the session. Needs to be flushed."""
        try:
            checked_entities = await self.pass_insert_checks(session, entities)
        except Exception as e:
            logger.error(f"Error adding entities to session: {e}")
            raise e

        session.add_all(checked_entities)
        logger.debug(f"Added entities to session: {checked_entities}")
        return checked_entities

    async def get_by_other_params(
        self, session: AsyncSession, **kwargs: Any
    ) -> list[Any]:
        """Gets an entity by other parameters."""
        try:
            assert kwargs
            assert all(key in self.__dict_keys() for key in kwargs.keys())
        except AssertionError as e:
            logger.error(f"Error getting entity by other parameters: {e}")
            raise e

        query = select(self.model_class).where(
            *[getattr(self.model_class, key) == value for key, value in kwargs.items()]
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, session: AsyncSession, entity_id: int) -> list[Any]:
        """Gets an entity by its ID."""
        try:
            assert entity_id
            assert isinstance(entity_id, int)
        except AssertionError as e:
            logger.error(f"Error getting entity by ID: {e}")
            raise ValueError("Invalid entity ID") from e

        query = select(self.model_class).where(self.model_class.object_id == entity_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_all(self, session: AsyncSession) -> list[Any]:
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
            logger.debug(f"Created entities in session: {response}")
            return response
        else:
            response = await self.add_one(session, entity)
            await session.flush()
            await session.refresh(response)
            logger.debug(f"Created entity in session: {len(response)}")
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

    @overload
    async def is_present(self, session: AsyncSession, entity_id: int) -> bool: ...

    @overload
    async def is_present(self, session: AsyncSession, **kwargs: Any) -> bool: ...

    async def is_present(
        self, session: AsyncSession, entity_id: int | None = None, **kwargs: Any
    ) -> bool:
        """Checks if an entity exists by its ID or other parameters."""
        if entity_id:
            return await self.is_present_one(session, entity_id)
        else:
            return await self.is_present_many(session, **kwargs)

    async def is_present_one(self, session: AsyncSession, entity_id: int) -> bool:
        """Checks if an entity exists by its ID."""
        result = await self.get_by_id(session, entity_id)
        try:
            assert result
            assert len(result) != 0
            return True
        except AssertionError:
            return False
        except Exception as e:
            logger.error(f"Error checking if entity is present: {e}")
            raise e

    async def is_present_many(self, session: AsyncSession, **kwargs: Any) -> bool:
        """Checks if an entity exists by other parameters."""
        result = await self.get_by_other_params(session, **kwargs)
        try:
            assert result
            assert len(result) != 0
            return True
        except AssertionError:
            return False
        except Exception as e:
            logger.error(f"Error checking if entity is present: {e}")
            raise e

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
        try:
            if isinstance(entity, list):
                return await self.__insert_check_for_many(session, entity)
            else:
                return await self.__insert_check_for_one(session, entity)
        except EntityAlreadyExistsError as e:
            raise e
        except Exception as e:
            logger.error(f"Unknown error passing insert checks: {e}")
            raise e

    async def __insert_check_for_many(
        self, session: AsyncSession, entities: list[T]
    ) -> list[T]:
        """Private method. Checks if entities are exists in db and validates them."""
        checked_entities: list[T] = []

        for entity in entities:
            try:
                entity = await self.__insert_check_for_one(session, entity)
            except EntityAlreadyExistsError:
                continue
            except Exception as e:
                logger.error(f"Unknown error passing insert checks: {e}")
                raise e

            checked_entities.append(entity)

        try:
            assert len(checked_entities) > 0
        except AssertionError as e:
            logger.error(f"Error validating entities: {e}")
            raise e

        return checked_entities

    async def __insert_check_for_one(self, session: AsyncSession, entity: T) -> T:
        """Private method. Checks if entity is exists in db and"""
        try:
            assert not await self.is_present(session, entity.object_id)
            entity = self.model_class.model_validate(entity)
        except AssertionError as e:
            raise EntityAlreadyExistsError(
                entity.object_id, self.model_class.__name__
            ) from e
        except ValidationError as e:
            logger.error(f"Failed to validate entity: {e}")
            raise ValueError(f"Invalid entity: {e}") from e
        except Exception as e:
            logger.error(f"Unknown error adding entity: {e}")
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
