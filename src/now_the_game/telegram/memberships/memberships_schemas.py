"""
ChatMembership-specific schema definitions.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from pyrogram.types import ChatMember, ChatMemberUpdated, Message
from sqlmodel import Field, Relationship

from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.shared.base import BaseSchema
from src.shared.events import EventPayload

if TYPE_CHECKING:
    from src.api.users.users_schemas import UserTable
    from src.now_the_game.telegram.chats.chats_schemas import ChatTable

logger = logging.getLogger("deus-vult.telegram.memberships")

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
TABLES
"""


class ChatMembershipBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id", primary_key=True, index=True)
    chat_id: int = Field(foreign_key="chats.object_id", primary_key=True, index=True)
    joined_at: datetime = Field(default=datetime.now())


class ChatMembershipTable(ChatMembershipBase, table=True):
    __tablename__ = "chat_members"  # type: ignore

    # --- Relationships ---
    chat: "ChatTable" = Relationship(back_populates="chat_members")
    user: "UserTable" = Relationship(back_populates="chat_members")
    # --- End Relationships ---

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
            logger.error(
                "Error creating chat membership from pyrogram message: %s",
                e,
            )
            raise PyrogramConversionError(
                f"Error creating chat membership from pyrogram message: {e}",
            ) from e
