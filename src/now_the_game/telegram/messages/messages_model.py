from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .messages_schemas import MessageBase


class MessageModel(BaseModel[MessageBase]):
    def __init__(self):
        super().__init__(MessageBase)

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int
    ) -> list[MessageBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, message_id: int
    ) -> list[MessageBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, user_id: int
    ) -> list[MessageBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, user_id: int, message_id: int
    ) -> list[MessageBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
        message_id: int | None = None,
    ) -> list[MessageBase]:
        if chat_id and message_id:
            return await self.__get_by_chat_id_and_message_id(
                session, chat_id, message_id
            )
        elif chat_id:
            return await self.__get_by_chat_id(session, chat_id)
        elif user_id and message_id:
            return await self.__get_by_user_id_and_message_id(
                session, user_id, message_id
            )
        elif user_id:
            return await self.__get_by_user_id(session, user_id)
        elif message_id:
            return await self.get_by_id(session, message_id)
        else:
            return await self.get_all(session)

    async def __get_by_chat_id(
        self, session: AsyncSession, chat_id: int
    ) -> list[MessageBase]:
        query = select(MessageBase).where(MessageBase.chat_id == chat_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def __get_by_chat_id_and_message_id(
        self, session: AsyncSession, chat_id: int, message_id: int
    ) -> list[MessageBase]:
        query = select(MessageBase).where(
            MessageBase.chat_id == chat_id, MessageBase.object_id == message_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def __get_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> list[MessageBase]:
        query = select(MessageBase).where(MessageBase.user_id == user_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def __get_by_user_id_and_message_id(
        self, session: AsyncSession, user_id: int, message_id: int
    ) -> list[MessageBase]:
        query = select(MessageBase).where(
            MessageBase.user_id == user_id, MessageBase.object_id == message_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())


message_model = MessageModel()
