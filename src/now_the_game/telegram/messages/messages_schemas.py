"""
Message-specific schema definitions.
This module re-exports the Message-related schemas from the central schema module.
"""

import logging
from enum import Enum

from pyrogram.client import Client
from pyrogram.types import Message
from sqlmodel import Field

from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.now_the_game.telegram.telegram_interfaces import IMessageEvent
from src.shared.base import BaseSchema
from src.shared.event_registry import MessageTopics
from src.shared.events import EventPayload

logger = logging.getLogger("deus-vult.telegram.messages")


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
    user_id: int = Field(foreign_key="users.object_id", index=True)
    chat_id: int = Field(foreign_key="chats.object_id", index=True)

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
            logger.error(
                "Error creating message from pyrogram message: %s",
                e,
            )
            raise PyrogramConversionError(
                "Error creating message from pyrogram message: %s",
                e,
            ) from e
