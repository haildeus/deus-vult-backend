import logging
from typing import overload

from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.now_the_game.telegram.polls.polls_schemas import (
    PollBase,
    PollOptionsBase,
    PollOptionTable,
    PollTable,
)
from src.shared.base import BaseModel, OverloadParametersError
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.telegram.polls")


class PollModel(BaseModel[PollTable]):
    """
    Model for polls
    """

    def __init__(self):
        super().__init__(PollTable)

    @overload
    async def get(self, session: AsyncSession) -> list[PollBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, chat_id: int) -> list[PollBase]: ...

    @overload
    async def get(
        self, session: AsyncSession, *, chat_id: int, message_id: int
    ) -> list[PollBase]: ...

    @overload
    async def get(self, session: AsyncSession, *, poll_id: int) -> list[PollBase]: ...

    @async_traced_function
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
            return await self.get_by_other_params(
                session,
                chat_id=chat_id,
                message_id=message_id,
                object_id=poll_id,
            )
        elif chat_id and message_id:
            return await self.get_by_other_params(
                session, chat_id=chat_id, message_id=message_id
            )
        elif chat_id:
            return await self.get_by_other_params(session, chat_id=chat_id)
        elif poll_id:
            return await self.get_by_id(session, poll_id)
        else:
            return await self.get_all(session)

    async def is_poll(self, message: Message) -> bool:
        try:
            assert message.poll
            return True
        except AssertionError:
            return False


class PollOptionModel(BaseModel[PollOptionTable]):
    """
    Model for poll options
    """

    def __init__(self):
        super().__init__(PollOptionTable)

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

    @async_traced_function
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
            logger.error("Error getting poll option: %s", e)
            raise OverloadParametersError("Function has too many parameters") from e

        if poll_id and option_id:
            return await self.get_by_other_params(
                session, poll_id=poll_id, object_id=option_id
            )
        elif poll_id:
            return await self.get_by_other_params(session, poll_id=poll_id)
        elif option_id:
            return await self.get_by_id(session, option_id)
        else:
            return await self.get_all(session)

    async def is_poll(self, message: Message) -> bool:
        try:
            assert message.poll
            return True
        except AssertionError:
            return False


poll_model = PollModel()
poll_option_model = PollOptionModel()
