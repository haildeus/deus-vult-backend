"""
Message-specific schema definitions.
This module re-exports the Message-related schemas from the central schema module.
"""

from enum import Enum

from pyrogram.client import Client
from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from src.now_the_game import logger
from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.now_the_game.telegram.telegram_interfaces import IMessageEvent
from src.shared.base import BaseSchema
from src.shared.event_registry import MessageTopics
from src.shared.events import EventPayload


class MessageType(Enum):
    TEXT = "text"
    MEDIA = "media"
    POLL = "poll"


"""
MODELS
"""


class AddMessagePayload(EventPayload):
    client: Client
    message: Message
    db_session: AsyncSession


"""
EVENTS
"""


class AddMessageEvent(IMessageEvent):
    topic: str = MessageTopics.MESSAGE_CREATE.value
    payload: AddMessagePayload  # type: ignore


"""
TABLES
"""


class MessageBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")

    message_type: MessageType = Field(default=MessageType.TEXT)
    content: str = Field(min_length=1, max_length=4096)


class MessageTable(MessageBase, table=True):
    __tablename__ = "messages"  # type: ignore

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "MessageTable":
        """Create a message from a pyrogram message"""

        try:
            return cls(
                object_id=message.id,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                content=message.text,
            )
        except Exception as e:
            logger.error(f"Error creating message from pyrogram message: {e}")
            raise PyrogramConversionError(
                f"Error creating message from pyrogram message: {e}"
            ) from e
