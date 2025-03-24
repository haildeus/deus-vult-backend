"""
This module exists to resolve circular imports between schema definitions.
All schema classes are imported and re-exported from this central location.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import model_validator
from pyrogram.enums import ChatType as PyrogramChatType
from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, Relationship, select

from .. import logger
from ..core.base import BaseSchema
from .telegram_exceptions import PyrogramConversionError

"""
Enums
"""


class PollType(Enum):
    QUIZ = "quiz"
    POLL = "poll"


class ChatType(Enum):
    USER = "user"
    CHAT = "chat"
    CHANNEL = "channel"


class MessageType(Enum):
    TEXT = "text"
    MEDIA = "media"
    POLL = "poll"


"""
Base classes
"""


class UserBase(BaseSchema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    is_premium: bool = Field(default=False)
    bio: str | None = Field(default=None, min_length=1, max_length=255)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "UserBase":
        """Create a user from a pyrogram message"""

        return cls(
            object_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            is_premium=message.from_user.is_premium,
        )


class ChatBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)

    chat_type: ChatType = Field(default=ChatType.USER)
    is_participant: bool = Field(default=False)

    @model_validator(mode="before")
    def validate_chat_type(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("is_participant") and values.get("chat_type") == ChatType.USER:
            raise ValueError("User cannot be a participant")
        return values

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "ChatBase":
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


class ChatMembershipBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")
    joined_at: datetime = Field(default=datetime.now())

    @classmethod
    async def validate_entities_exist(
        cls, session: AsyncSession, values: dict[str, Any]
    ) -> bool:
        """Validate that user and chat exist before creating a chat member"""

        user_id = values.get("user_id")
        chat_id = values.get("chat_id")

        if not user_id or not chat_id:
            return False

        user = await session.execute(
            select(UserSchema).where(UserSchema.object_id == user_id)
        )
        chat = await session.execute(
            select(ChatSchema).where(ChatSchema.object_id == chat_id)
        )

        return (
            user.scalar_one_or_none() is not None
            and chat.scalar_one_or_none() is not None
        )

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


class MessageBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")

    message_type: MessageType = Field(default=MessageType.TEXT)
    content: str = Field(min_length=1, max_length=4096)

    @classmethod
    async def validate_entities_exist(
        cls, session: AsyncSession, user_id: int, chat_id: int
    ) -> bool:
        """Validate that user and chat exist before creating a message"""
        if not user_id or not chat_id:
            return False

        user = await session.execute(
            select(UserSchema).where(UserSchema.object_id == user_id)
        )
        chat = await session.execute(
            select(ChatSchema).where(ChatSchema.object_id == chat_id)
        )

        return (
            user.scalar_one_or_none() is not None
            and chat.scalar_one_or_none() is not None
        )

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "MessageBase":
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


class PollBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.object_id")
    message_id: int = Field(foreign_key="messages.object_id")
    question: str = Field(min_length=1, max_length=300)
    poll_type: PollType = Field(default=PollType.POLL)
    is_anonymous: bool = Field(default=True)
    close_date: datetime | None = Field(default=None)

    @classmethod
    async def validate_entities_exist(
        cls, session: AsyncSession, values: dict[str, Any]
    ) -> bool:
        """Validate that chat and message exist before creating a poll"""

        chat_id = values.get("chat_id")
        message_id = values.get("message_id")

        if not chat_id or not message_id:
            return False

        chat = await session.execute(
            select(ChatSchema).where(ChatSchema.object_id == chat_id)
        )
        message = await session.execute(
            select(MessageSchema).where(MessageSchema.object_id == message_id)
        )

        return (
            chat.scalar_one_or_none() is not None
            and message.scalar_one_or_none() is not None
        )

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "PollBase":
        """Create a poll from a pyrogram message"""
        try:
            assert message.poll
        except AssertionError as e:
            raise PyrogramConversionError("Message is not a poll") from e

        return cls(
            chat_id=message.chat.id,
            message_id=message.id,
            question=message.poll.question,
            poll_type=PollType.POLL,
            is_anonymous=message.poll.is_anonymous,
            close_date=message.poll.close_date,
        )


class PollOptionsBase(BaseSchema):
    poll_id: int = Field(foreign_key="polls.object_id")
    option_text: str = Field(min_length=1, max_length=100)

    @classmethod
    async def validate_entities_exist(
        cls, session: AsyncSession, values: dict[str, Any]
    ) -> bool:
        """Validate that poll exists before creating a poll option"""

        poll_id = values.get("poll_id")

        if not poll_id:
            return False

        poll = await session.execute(
            select(PollSchema).where(PollSchema.object_id == poll_id)
        )

        return poll.scalar_one_or_none() is not None

    @classmethod
    async def from_pyrogram(
        cls, poll_id: int, option_position: int, message: Message
    ) -> "PollOptionsBase":
        """Create a poll option from a pyrogram message"""
        try:
            assert message.poll
            assert option_position
            assert isinstance(option_position, int)
            assert option_position < len(message.poll.options)
            assert option_position >= 0
        except AssertionError as e:
            raise PyrogramConversionError(
                f"Error creating poll option from pyrogram message: {e}"
            ) from e

        return cls(
            poll_id=poll_id,
            option_text=message.poll.options[option_position].text,
        )


"""
Concrete model classes with relationships
"""


class UserSchema(UserBase, table=True):
    __tablename__ = "users"  # type: ignore

    # Relationships
    chat_members: list["ChatMembershipSchema"] = Relationship(back_populates="user")
    messages: list["MessageSchema"] = Relationship(back_populates="user")

    # A user must be associated with at least one chat
    chats: list["ChatSchema"] = Relationship(
        back_populates="users", link_model=ChatMembershipBase
    )


class ChatSchema(ChatBase, table=True):
    __tablename__ = "chats"  # type: ignore

    # Relationships
    chat_members: list["ChatMembershipSchema"] = Relationship(back_populates="chat")
    messages: list["MessageSchema"] = Relationship(back_populates="chat")
    polls: list["PollSchema"] = Relationship(back_populates="chat")

    # Users in this chat
    users: list["UserSchema"] = Relationship(
        back_populates="chats", link_model=ChatMembershipBase
    )


class ChatMembershipSchema(ChatMembershipBase, table=True):
    __tablename__ = "chat_members"  # type: ignore

    chat: ChatSchema = Relationship(back_populates="chat_members")
    user: UserSchema = Relationship(back_populates="chat_members")


class MessageSchema(MessageBase, table=True):
    __tablename__ = "messages"  # type: ignore

    chat: ChatSchema = Relationship(back_populates="messages")
    user: UserSchema = Relationship(back_populates="messages")
    polls: list["PollSchema"] = Relationship(back_populates="message")


class PollSchema(PollBase, table=True):
    __tablename__ = "polls"  # type: ignore

    options: list["PollOptionSchema"] = Relationship(back_populates="poll")
    message: MessageSchema = Relationship(back_populates="polls")
    chat: ChatSchema = Relationship(back_populates="polls")


class PollOptionSchema(PollOptionsBase, table=True):
    __tablename__ = "poll_options"  # type: ignore

    poll: PollSchema = Relationship(back_populates="options")


"""
Orchestrator schemas
"""


class MessageCore(BaseSchema):
    message: MessageBase
    chat: ChatBase
    user: UserBase
    chat_membership: ChatMembershipBase

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "MessageCore":
        """Create a message core from a pyrogram message"""

        try:
            return cls(
                message=await MessageBase.from_pyrogram(message),
                chat=await ChatBase.from_pyrogram(message),
                user=await UserBase.from_pyrogram(message),
                chat_membership=await ChatMembershipBase.from_pyrogram(message),
            )
        except Exception as e:
            logger.error(f"Error creating message core from pyrogram message: {e}")
            raise PyrogramConversionError(
                f"Error creating message core from pyrogram message: {e}"
            ) from e
