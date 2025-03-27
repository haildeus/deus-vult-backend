"""
Chat-specific schema definitions.
This module re-exports the Chat-related schemas from the central schema module.
"""

from enum import Enum
from typing import Any

from pydantic import model_validator
from pyrogram.client import Client
from pyrogram.enums import ChatType as PyrogramChatType
from pyrogram.types import ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from src import BaseSchema, EventPayload
from src.now_the_game import logger
from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.now_the_game.telegram.telegram_interfaces import IChatEvent

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "telegram.chats"

"""
ENUMS
"""


class ChatTopics(Enum):
    CHAT_ADDED = f"{EVENT_BUS_PREFIX}.added"


class ChatType(Enum):
    USER = "user"
    CHAT = "chat"
    CHANNEL = "channel"


"""
MODELS
"""


class AddChatEventPayload(EventPayload):
    client: Client
    message: Message | ChatMemberUpdated
    db_session: AsyncSession


"""
EVENTS
"""


class AddChatEvent(IChatEvent):
    topic: str = ChatTopics.CHAT_ADDED.value
    payload: AddChatEventPayload  # type: ignore


"""
TABLES
"""


class ChatBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)

    chat_type: ChatType = Field(default=ChatType.USER)
    is_participant: bool = Field(default=False)

    @model_validator(mode="before")
    def validate_chat_type(cls, values: Any) -> Any:
        if values.is_participant and values.chat_type == ChatType.USER:
            raise ValueError("User cannot be a participant")
        return values


class ChatTable(ChatBase, table=True):
    __tablename__ = "chats"  # type: ignore

    @classmethod
    async def from_pyrogram(cls, message: Message | ChatMemberUpdated) -> "ChatTable":
        """Create a chat from a pyrogram message"""

        try:
            if message.chat.type == PyrogramChatType.PRIVATE:
                chat_type = ChatType.USER
            elif message.chat.type == PyrogramChatType.CHANNEL:
                chat_type = ChatType.CHANNEL
            else:
                chat_type = ChatType.CHAT

            return cls(
                object_id=message.chat.id,
                name=message.chat.title
                or message.chat.first_name
                or message.chat.username,
                username=message.chat.username,
                chat_type=chat_type,
            )
        except Exception as e:
            logger.error(f"Error creating chat from pyrogram message: {e}")
            raise PyrogramConversionError(
                f"Error creating chat from pyrogram message: {e}"
            ) from e
