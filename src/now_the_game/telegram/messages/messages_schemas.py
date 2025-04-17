"""
Message-specific schema definitions.
This module re-exports the Message-related schemas from the central schema module.
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING

from pyrogram.client import Client
from pyrogram.types import Message
from sqlmodel import Field, Relationship

from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.shared.base import BaseSchema
from src.shared.events import EventPayload

if TYPE_CHECKING:
    from src.now_the_game.telegram.chats.chats_schemas import ChatTable
    from src.now_the_game.telegram.polls.polls_schemas import PollTable
    from src.now_the_game.telegram.users.users_schemas import UserTable

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
TABLES
"""


class MessageBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id", index=True)
    chat_id: int = Field(foreign_key="chats.object_id", index=True)

    message_type: MessageType = Field(default=MessageType.TEXT)
    content: str = Field(min_length=1, max_length=4096)


class MessageTable(MessageBase, table=True):
    __tablename__ = "messages"

    # --- Relationships ---
    user: "UserTable" = Relationship(back_populates="messages")
    chat: "ChatTable" = Relationship(back_populates="messages")
    polls: list["PollTable"] = Relationship(
        back_populates="message", sa_relationship_kwargs={"lazy": "selectin"}
    )
    # --- End Relationships ---

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
                message="Error creating message from pyrogram message: {e}",
            ) from e
