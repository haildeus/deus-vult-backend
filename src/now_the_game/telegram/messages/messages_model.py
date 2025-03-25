from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.base import BaseModel
from .messages_schemas import MessageBase, MessageTable


class MessageModel(BaseModel[MessageTable]):
    def __init__(self):
        super().__init__(MessageTable)

    @overload
    async def get(self, session: AsyncSession) -> list[MessageBase]: ...

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
            return await self.get_by_other_params(
                session, chat_id=chat_id, object_id=message_id
            )
        elif chat_id:
            return await self.get_by_other_params(session, chat_id=chat_id)
        elif user_id and message_id:
            return await self.get_by_other_params(
                session, user_id=user_id, object_id=message_id
            )
        elif user_id:
            return await self.get_by_other_params(session, user_id=user_id)
        elif message_id:
            return await self.get_by_id(session, message_id)
        else:
            return await self.get_all(session)


message_model = MessageModel()
