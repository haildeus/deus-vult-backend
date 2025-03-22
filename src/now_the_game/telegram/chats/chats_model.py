from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .chats_schemas import ChatMembershipSchema, ChatSchema


class ChatModel(BaseModel[ChatSchema]):
    def __init__(self):
        super().__init__(ChatSchema)

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> ChatSchema | None:
        result = await session.execute(
            select(ChatSchema).where(ChatSchema.username == username)
        )
        return result.scalar_one_or_none()


class ChatMembershipModel(BaseModel[ChatMembershipSchema]):
    def __init__(self):
        super().__init__(ChatMembershipSchema)


chat_model = ChatModel()
chat_membership_model = ChatMembershipModel()
