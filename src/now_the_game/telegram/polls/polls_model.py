from typing import overload

from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ... import logger
from ...core.base import BaseModel, OverloadParametersError
from .polls_schemas import PollBase, PollOptionsBase


class PollModel(BaseModel[PollBase]):
    """
    Model for polls
    """

    def __init__(self):
        super().__init__(PollBase)

    @overload
    async def get(self, session: AsyncSession, *, chat_id: int) -> list[PollBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, message_id: int
    ) -> list[PollBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, poll_id: int) -> list[PollBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        chat_id: int | None = None,
        message_id: int | None = None,
        poll_id: int | None = None,
    ) -> list[PollBase]:
        """Get a poll by chat ID, message ID, or poll ID"""

        if chat_id and message_id and poll_id:
            return await self.get_for_chat_message_poll_id(
                session, chat_id, message_id, poll_id
            )
        elif chat_id and message_id:
            return await self.get_for_chat_message_id(session, chat_id, message_id)
        elif chat_id:
            return await self.get_for_chat(session, chat_id)
        elif poll_id:
            return await self.get_by_id(session, poll_id)
        else:
            return await self.get_all(session)

    # TODO: Add an order by created_at condition
    async def get_for_chat(
        self, session: AsyncSession, chat_id: int, limit: int = 100
    ) -> list[PollBase]:
        """Get the latest polls for a chat"""
        query = select(PollBase).where(PollBase.chat_id == chat_id).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_chat_message_id(
        self, session: AsyncSession, chat_id: int, message_id: int, limit: int = 100
    ) -> list[PollBase]:
        """Get the latest polls for a chat message"""
        query = (
            select(PollBase)
            .where(PollBase.chat_id == chat_id, PollBase.message_id == message_id)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_chat_message_poll_id(
        self,
        session: AsyncSession,
        chat_id: int,
        message_id: int,
        poll_id: int,
        limit: int = 100,
    ) -> list[PollBase]:
        """Get the latest polls for a chat message poll ID"""
        query = (
            select(PollBase)
            .where(
                PollBase.chat_id == chat_id,
                PollBase.message_id == message_id,
                PollBase.object_id == poll_id,
            )
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def is_poll(self, message: Message) -> bool:
        try:
            assert message.poll
            return True
        except AssertionError:
            return False


class PollOptionModel(BaseModel[PollOptionsBase]):
    """
    Model for poll options
    """

    def __init__(self):
        super().__init__(PollOptionsBase)

    @overload
    async def get(self, session: AsyncSession) -> list[PollOptionsBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, poll_id: int
    ) -> list[PollOptionsBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, option_id: int
    ) -> list[PollOptionsBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, poll_id: int, option_id: int
    ) -> list[PollOptionsBase]: ...

    async def get(
        self,
        session: AsyncSession,
        *,
        poll_id: int | None = None,
        option_id: int | None = None,
    ) -> list[PollOptionsBase]:
        """Get a poll option by poll ID or option ID"""
        try:
            assert sum(arg is not None for arg in (poll_id, option_id)) <= 1
        except AssertionError as e:
            logger.error(f"Error getting poll option: {e}")
            raise OverloadParametersError("Function has too many parameters") from e

        if poll_id and option_id:
            return await self.get_for_poll_option_id(session, poll_id, option_id)
        elif poll_id:
            return await self.get_for_poll_id(session, poll_id)
        elif option_id:
            return await self.get_by_id(session, option_id)
        else:
            return await self.get_all(session)

    async def get_for_poll_id(
        self, session: AsyncSession, poll_id: int
    ) -> list[PollOptionsBase]:
        """Get all options for a poll"""
        try:
            assert poll_id
            assert isinstance(poll_id, int)
        except AssertionError as e:
            logger.error(f"Error getting poll options: {e}")
            raise e
        query = select(PollOptionsBase).where(PollOptionsBase.poll_id == poll_id)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_for_poll_option_id(
        self,
        session: AsyncSession,
        poll_id: int,
        option_id: int,
    ) -> list[PollOptionsBase]:
        """Get a poll option by poll ID and option ID"""
        try:
            assert poll_id
            assert isinstance(poll_id, int)
            assert option_id
            assert isinstance(option_id, int)
        except AssertionError as e:
            logger.error(f"Error getting poll options: {e}")
            raise e
        query = select(PollOptionsBase).where(
            PollOptionsBase.poll_id == poll_id, PollOptionsBase.object_id == option_id
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def is_poll(self, message: Message) -> bool:
        try:
            assert message.poll
            return True
        except AssertionError:
            return False


poll_model = PollModel()
poll_option_model = PollOptionModel()
