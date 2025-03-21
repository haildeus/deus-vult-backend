from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .polls_schemas import Poll, PollOptions


class PollsModel(BaseModel[Poll]):
    def __init__(self):
        super().__init__(Poll)

    async def get_with_options(
        self, session: AsyncSession, poll_id: int
    ) -> Poll | None:
        query = select(Poll).where(Poll.poll_id == poll_id)
        result = await session.exec(query)
        poll = result.scalar_one_or_none()
        if poll:
            query = select(PollOptions).where(PollOptions.poll_id == poll_id)
            result = await session.exec(query)
            poll.options = result.scalars().all()
        return poll

    async def get_by_message_id(
        self, session: AsyncSession, message_id: int
    ) -> Poll | None:
        query = select(Poll).where(Poll.message_id == message_id)
        result = await session.exec(query)
        return result.scalar_one_or_none()

    async def get_recent_for_chat(
        self, session: AsyncSession, chat_id: int, limit: int = 10
    ) -> list[Poll]:
        query = (
            select(Poll)
            .where(Poll.chat_id == chat_id)
            .order_by(Poll.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(query)
        return result.scalars().all()


class PollOptionsModel(BaseModel[PollOptions]):
    def __init__(self):
        super().__init__(PollOptions)

    async def get_by_poll_id(
        self, session: AsyncSession, poll_id: int
    ) -> list[PollOptions]:
        query = select(PollOptions).where(PollOptions.poll_id == poll_id)
        result = await session.exec(query)
        return result.scalars().all()


poll_model = PollsModel()
poll_options_model = PollOptionsModel()
