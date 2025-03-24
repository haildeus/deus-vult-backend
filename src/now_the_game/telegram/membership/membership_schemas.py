"""
ChatMembership-specific schema definitions.
"""

from datetime import datetime

from pyrogram.types import Message
from sqlmodel import Field

from ... import logger
from ...core.base import BaseSchema
from ..telegram_exceptions import PyrogramConversionError


class ChatMembershipBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")
    joined_at: datetime = Field(default=datetime.now())

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "ChatMembershipBase":
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
