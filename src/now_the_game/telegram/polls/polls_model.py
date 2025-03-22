from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .polls_schemas import PollSchema, PollOptionSchema


class PollsModel(BaseModel[PollSchema]):
    def __init__(self):
        super().__init__(PollSchema)

    async def get_with_options(
        self, session: AsyncSession, poll_id: int
    ) -> PollSchema | None:
        query = select(PollSchema).where(PollSchema.poll_id == poll_id)
        result = await session.exec(query)
        poll = result.scalar_one_or_none()
        if poll:
            query = select(PollOptionSchema).where(PollOptionSchema.poll_id == poll_id)
            result = await session.exec(query)
            poll.options = result.scalars().all()
        return poll

    async def get_by_message_id(
        self, session: AsyncSession, message_id: int
    ) -> PollSchema | None:
        query = select(PollSchema).where(PollSchema.message_id == message_id)
        result = await session.exec(query)
        return result.scalar_one_or_none()

    async def get_recent_for_chat(
        self, session: AsyncSession, chat_id: int, limit: int = 10
    ) -> list[PollSchema]:
        query = (
            select(PollSchema)
            .where(PollSchema.chat_id == chat_id)
            .order_by(PollSchema.created_at.desc())
            .limit(limit)
        )
        result = await session.exec(query)
        return result.scalars().all()


class PollOptionsModel(BaseModel[PollOptionSchema]):
    def __init__(self):
        super().__init__(PollOptionSchema)

    async def get_by_poll_id(
        self, session: AsyncSession, poll_id: int
    ) -> list[PollOptionSchema]:
        query = select(PollOptionSchema).where(PollOptionSchema.poll_id == poll_id)
        result = await session.exec(query)
        return result.scalars().all()


poll_model = PollsModel()
poll_options_model = PollOptionsModel()
