import logging
from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.now_the_game.telegram.memberships.memberships_schemas import (
    ChatMembershipBase,
    ChatMembershipTable,
)
from src.shared.base import BaseModel, EntityAlreadyExistsError, EntityNotFoundError
from src.shared.observability.traces import async_traced_function


logger = logging.getLogger("deus-vult.telegram.memberships")


class ChatMembershipModel(BaseModel[ChatMembershipTable]):
    def __init__(self):
        super().__init__(ChatMembershipTable)

    @async_traced_function
    async def has_membership(
        self, session: AsyncSession, user_id: int, chat_id: int
    ) -> bool:
        """Checks if a user has a membership to a chat"""
        query = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.chat_id == chat_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @overload
    async def get(self, session: AsyncSession) -> list[ChatMembershipBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, user_id: int, chat_id: None = None
    ) -> list[ChatMembershipBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, user_id: None = None, chat_id: int
    ) -> list[ChatMembershipBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, user_id: int, chat_id: int
    ) -> list[ChatMembershipBase]: ...

    @async_traced_function
    async def get(
        self,
        session: AsyncSession,
        *,
        user_id: int | None = None,
        chat_id: int | None = None,
    ) -> list[ChatMembershipBase] | None:
        """Takes in user ID or chat ID, returns ChatMembershipSchema"""
        if user_id and chat_id:
            return await self.get_by_other_params(
                session, user_id=user_id, chat_id=chat_id
            )
        elif user_id:
            return await self.get_by_other_params(session, user_id=user_id)
        elif chat_id:
            return await self.get_by_other_params(session, chat_id=chat_id)

        return await self.get_all(session)

    @async_traced_function
    async def remove_secure(
        self,
        session: AsyncSession,
        user_id: int,
        chat_id: int,
    ) -> bool:
        """Removes a ChatMembershipSchema from the database"""
        query = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.chat_id == chat_id,
        )
        result = await session.execute(query)
        result = list(result.scalars().all())
        try:
            assert len(result) == 1
        except AssertionError as e:
            raise EntityNotFoundError(entity_id=f"{user_id} in {chat_id}") from e
        except Exception as e:
            logger.error(f"Error removing ChatMembershipSchema: {e}")
            raise e

        await session.delete(result[0])
        return True

    @async_traced_function
    async def not_exists(
        self, session: AsyncSession, user_id: int, chat_id: int
    ) -> bool:
        """Checks if a ChatMembershipSchema exists in the database"""
        query = select(self.model_class).where(
            self.model_class.user_id == user_id,
            self.model_class.chat_id == chat_id,
        )
        result = await session.execute(query)
        result = list(result.scalars().all())
        try:
            assert len(result) == 0
        except AssertionError as e:
            transformed_entity = f"{user_id} in {chat_id}"
            raise EntityAlreadyExistsError(
                entity=transformed_entity, entity_type=self.model_class.__name__
            ) from e
        except Exception as e:
            logger.error(f"Error checking if ChatMembershipSchema exists: {e}")
            raise e

        return len(result) == 0


chat_membership_model = ChatMembershipModel()
