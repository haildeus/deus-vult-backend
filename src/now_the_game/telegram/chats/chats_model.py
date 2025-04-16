import logging
from typing import overload

from sqlalchemy.ext.asyncio import AsyncSession

from src.now_the_game.telegram.chats.chats_schemas import ChatBase, ChatTable, ChatType
from src.shared.base import BaseModel, OverloadParametersError
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.telegram.chats")


class ChatModel(BaseModel[ChatTable]):
    def __init__(self):
        super().__init__(ChatTable)

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

    @async_traced_function
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
            logger.error("Error getting chat: %s", e)
            raise OverloadParametersError("Function has too many parameters") from e

        if username:
            return await self.get_by_other_params(session, username=username)
        elif chat_type:
            return await self.get_by_other_params(session, chat_type=chat_type)
        elif name:
            return await self.get_by_other_params(session, name=name)
        elif chat_id:
            return await self.get_by_id(session, chat_id)
        else:
            return await self.get_all(session)


chat_model = ChatModel()
