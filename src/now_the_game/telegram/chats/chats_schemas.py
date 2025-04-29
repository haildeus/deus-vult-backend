"""
Chat-specific schema definitions.
This module re-exports the Chat-related schemas from the central schema module.
"""

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import model_validator
from pyrogram.enums import ChatType as PyrogramChatType
from pyrogram.types import ChatMemberUpdated, Message
from sqlmodel import Field, Relationship, UniqueConstraint

from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.shared.base import BaseSchema
from src.shared.events import EventPayload

if TYPE_CHECKING:
    from src.api.users.users_schemas import UserTable
    from src.now_the_game.telegram.memberships.memberships_schemas import (
        ChatMembershipTable,
    )
    from src.now_the_game.telegram.messages.messages_schemas import MessageTable
    from src.now_the_game.telegram.polls.polls_schemas import PollTable

logger = logging.getLogger("deus-vult.telegram.chats")


class ChatType(Enum):
    USER = "user"
    CHAT = "chat"
    CHANNEL = "channel"


"""
MODELS
"""


class AddChatEventPayload(EventPayload):
    message: Message | ChatMemberUpdated


"""
TABLES
"""


class ChatBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)

    chat_type: ChatType = Field(default=ChatType.USER)
    chat_instance: int | None = Field(default=None, index=True, nullable=True)

    @model_validator(mode="before")
    def validate_chat_type(cls, values: Any) -> Any:
        if values.is_participant and values.chat_type == ChatType.USER:
            raise ValueError("User cannot be a participant")
        return values


class ChatTable(ChatBase, table=True):
    __tablename__ = "chats"  # type: ignore

    # --- Relationships ---
    chat_members: list["ChatMembershipTable"] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
    )
    messages: list["MessageTable"] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
    )
    polls: list["PollTable"] = Relationship(
        back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
    )
    users: list["UserTable"] = Relationship(
        back_populates="chats",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    __table_args__ = (
        # Ensure chat_instance is unique
        UniqueConstraint("chat_instance", name="uq_chats_chat_instance"),
    )

    # --- End Relationships ---
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
            logger.error("Error creating chat from pyrogram message: %s", e)
            raise PyrogramConversionError(
                f"Error creating chat from pyrogram message: {e}",
            ) from e
