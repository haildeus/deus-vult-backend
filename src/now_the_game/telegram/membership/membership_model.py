from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .membership_schemas import ChatMembershipSchema


class ChatMembershipModel(BaseModel[ChatMembershipSchema]):
    def __init__(self):
        super().__init__(ChatMembershipSchema)

    async def get_by_user_id(
        self, session: AsyncSession, user_id: int
    ) -> ChatMembershipSchema | None:
        """Takes in telegram ID, returns ChatMembershipSchema"""
        query = select(ChatMembershipSchema).where(
            ChatMembershipSchema.user_id == user_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_chat_id(
        self, session: AsyncSession, chat_id: int
    ) -> ChatMembershipSchema | None:
        """Takes in chat ID, returns ChatMembershipSchema"""
        query = select(ChatMembershipSchema).where(
            ChatMembershipSchema.chat_id == chat_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user_id_and_chat_id(
        self, session: AsyncSession, user_id: int, chat_id: int
    ) -> ChatMembershipSchema | None:
        """Takes in user ID and chat ID, returns ChatMembershipSchema"""
        query = select(ChatMembershipSchema).where(
            ChatMembershipSchema.user_id == user_id,
            ChatMembershipSchema.chat_id == chat_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()


chat_membership_model = ChatMembershipModel()
