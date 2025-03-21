from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ...core.base import BaseModel
from .chats_schemas import Chat, ChatMember


class ChatModel(BaseModel[Chat]):
    def __init__(self):
        super().__init__(Chat)

    async def get_by_username(
        self, session: AsyncSession, username: str
    ) -> Chat | None:
        result = await session.execute(select(Chat).where(Chat.username == username))
        return result.scalar_one_or_none()


class ChatMemberModel(BaseModel[ChatMember]):
    def __init__(self):
        super().__init__(ChatMember)


chat_model = ChatModel()
chat_member_model = ChatMemberModel()
