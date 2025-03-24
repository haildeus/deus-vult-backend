from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ... import logger
from ...core.base import BaseModel, OverloadParametersError
from .chats_schemas import ChatBase, ChatType


class ChatModel(BaseModel[ChatBase]):
    def __init__(self):
        super().__init__(ChatBase)

    @overload
    async def get(self, session: AsyncSession, *, chat_id: int) -> list[ChatBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, username: str) -> list[ChatBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_type: ChatType
    ) -> list[ChatBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, name: str) -> list[ChatBase]: ...

    @overload
    async def get(self, session: AsyncSession) -> list[ChatBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        username: str | None = None,
        chat_type: ChatType | None = None,
        name: str | None = None,
        chat_id: int | None = None,
    ) -> list[ChatBase]:
        """Get a chat by username, type, name, or ID"""
        try:
            # assert that only one of the arguments is provided
            assert (
                sum(arg is not None for arg in (username, chat_type, name, chat_id))
                <= 1
            )
        except AssertionError as e:
            logger.error(f"Error getting chat: {e}")
            raise OverloadParametersError("Function has too many parameters") from e

        if username:
            return await self.__get_by_username(session, username)
        elif chat_type:
            return await self.__get_by_type(session, chat_type)
        elif name:
            return await self.__get_by_name(session, name)
        elif chat_id:
            return await self.get_by_id(session, chat_id)
        else:
            return await self.get_all(session)

    async def __get_by_username(
        self, session: AsyncSession, username: str
    ) -> list[ChatBase]:
        """Get a chat by username"""
        try:
            assert username
            assert isinstance(username, str)
            assert len(username) >= 3
        except AssertionError as e:
            logger.error(f"Error getting chat by username: {e}")
            raise e
        query = select(ChatBase).where(ChatBase.username == username)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def __get_by_type(
        self, session: AsyncSession, chat_type: ChatType
    ) -> list[ChatBase]:
        """Get a chat by type"""
        try:
            assert chat_type
            assert isinstance(chat_type, ChatType)
        except AssertionError as e:
            logger.error(f"Error getting chat by type: {e}")
            raise e
        query = select(ChatBase).where(ChatBase.chat_type == chat_type)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def __get_by_name(self, session: AsyncSession, name: str) -> list[ChatBase]:
        """Get a chat by name"""
        try:
            assert name
            assert isinstance(name, str)
            assert len(name) >= 3
        except AssertionError as e:
            logger.error(f"Error getting chat by name: {e}")
            raise e
        query = select(ChatBase).where(ChatBase.name == name)
        result = await session.execute(query)
        return list(result.scalars().all())


chat_model = ChatModel()
