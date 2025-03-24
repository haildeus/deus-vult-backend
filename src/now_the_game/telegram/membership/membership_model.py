from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .membership_schemas import ChatMembershipBase


class ChatMembershipModel(BaseModel[ChatMembershipBase]):
    def __init__(self):
        super().__init__(ChatMembershipBase)

    async def has_membership(
        self, session: AsyncSession, user_id: int, chat_id: int
    ) -> bool:
        """Checks if a user has a membership to a chat"""
        query = select(ChatMembershipBase).where(
            ChatMembershipBase.user_id == user_id,
            ChatMembershipBase.chat_id == chat_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

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

    async def get(
        self,
        session: AsyncSession,
        *,
        user_id: int | None = None,
        chat_id: int | None = None,
    ) -> list[ChatMembershipBase] | None:
        """Takes in user ID or chat ID, returns ChatMembershipSchema"""
        if user_id and chat_id:
            return await self.get_by_user_id_and_chat_id(session, user_id, chat_id)
        elif user_id:
            return await self.get_by_user_id(session, user_id)
        elif chat_id:
            return await self.get_by_chat_id(session, chat_id)

        return await self.get_all(session)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> list[ChatMembershipBase]:
        """Takes in user ID, returns list of ChatMembershipSchema"""
        query = select(ChatMembershipBase).where(ChatMembershipBase.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_chat_id(
        self, session: AsyncSession, chat_id: int
    ) -> list[ChatMembershipBase]:
        """Takes in chat ID, returns ChatMembershipSchema"""
        query = select(ChatMembershipBase).where(ChatMembershipBase.chat_id == chat_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_user_id_and_chat_id(
        self, session: AsyncSession, user_id: int, chat_id: int
    ) -> list[ChatMembershipBase]:
        """Takes in user ID and chat ID, returns ChatMembershipSchema"""
        query = select(ChatMembershipBase).where(
            ChatMembershipBase.user_id == user_id,
            ChatMembershipBase.chat_id == chat_id,
        )
        result = await session.execute(query)
        return list(result.scalars().all())


chat_membership_model = ChatMembershipModel()
