"""
ChatMembership-specific schema definitions.
"""

from datetime import datetime

from pyrogram.types import ChatMember, ChatMemberUpdated, Message
from sqlmodel import Field

from src.now_the_game import logger
from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.now_the_game.telegram.telegram_interfaces import IMembershipChanged
from src.shared.base import BaseSchema
from src.shared.event_registry import MembershipTopics
from src.shared.events import EventPayload

"""
MODELS
"""


class AddChatMembershipPayload(EventPayload):
    message: Message


class ChangeChatMembershipPayload(EventPayload):
    chat_member_updated: ChatMemberUpdated
    updated_info: ChatMember
    new_member: bool


"""
EVENTS
"""


class ChangeChatMembershipEvent(IMembershipChanged):
    topic: str = MembershipTopics.MEMBERSHIP_UPDATE.value
    payload: ChangeChatMembershipPayload  # type: ignore


class AddChatMembershipEvent(IMembershipChanged):
    topic: str = MembershipTopics.MEMBERSHIP_CREATE.value
    payload: AddChatMembershipPayload  # type: ignore


"""
TABLES
"""


class ChatMembershipBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id", primary_key=True)
    chat_id: int = Field(foreign_key="chats.object_id", primary_key=True)
    joined_at: datetime = Field(default=datetime.now())


class ChatMembershipTable(ChatMembershipBase, table=True):
    __tablename__ = "chat_members"  # type: ignore

    @classmethod
    async def create(cls, user_id: int, chat_id: int) -> "ChatMembershipTable":
        try:
            assert user_id is not None
            assert chat_id is not None
        except AssertionError as e:
            raise ValueError("User ID and chat ID must be provided") from e

        return cls(user_id=user_id, chat_id=chat_id)

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "ChatMembershipTable":
        """Create a chat membership from a pyrogram message"""
        try:
            return cls(
                user_id=message.from_user.id,
                chat_id=message.chat.id,
            )
        except Exception as e:
            logger.error(f"Error creating chat membership from pyrogram message: {e}")
            raise PyrogramConversionError(
                f"Error creating chat membership from pyrogram message: {e}"
            ) from e
