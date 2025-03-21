"""
This module exists to resolve circular imports between schema definitions.
All schema classes are imported and re-exported from this central location.
"""

from datetime import datetime
from enum import Enum

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

from ..core.base import BaseSchema

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

    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class ChatBase(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)

    chat_type: ChatType = Field(default=ChatType.USER)
    is_participant: bool = Field(default=False)

    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

    @model_validator(mode="before")
    def validate_chat_type(cls, values):
        if values.get("is_participant") and values.get("chat_type") == ChatType.USER:
            raise ValueError("User cannot be a participant")
        return values


class ChatMemberBase(SQLModel):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")
    joined_at: datetime = Field(default=datetime.now())


class MessageBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id")
    chat_id: int = Field(foreign_key="chats.object_id")

    message_type: str = Field(min_length=1, max_length=100)

    content: str = Field(min_length=1, max_length=4096)
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class PollBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.chat_id")
    message_id: int = Field(foreign_key="messages.message_id")
    question: str = Field(min_length=1, max_length=300)
    poll_type: PollType = Field(default=PollType.POLL)
    is_anonymous: bool = Field(default=True)
    close_date: datetime | None = Field(default=None)

    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class PollOptionsBase(BaseSchema):
    poll_id: int = Field(foreign_key="polls.object_id")
    option_text: str = Field(min_length=1, max_length=100)

    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


"""
Concrete model classes with relationships
"""


class User(UserBase, table=True):
    __tablename__ = "users"

    chats: list["ChatMember"] = Relationship(back_populates="user")
    messages: list["Message"] = Relationship(back_populates="user")


class Chat(ChatBase, table=True):
    __tablename__ = "chats"

    members: list["ChatMember"] = Relationship(back_populates="chat")
    messages: list["Message"] = Relationship(back_populates="chat")


class ChatMember(ChatMemberBase, table=True):
    __tablename__ = "chat_members"

    chat: Chat = Relationship(back_populates="members")
    user: User = Relationship(back_populates="chats")


class Message(MessageBase, table=True):
    __tablename__ = "messages"

    chat: Chat = Relationship(back_populates="messages")
    user: User = Relationship(back_populates="messages")


class Poll(PollBase, table=True):
    __tablename__ = "polls"

    options: list["PollOptions"] = Relationship(back_populates="poll")


class PollOptions(PollOptionsBase, table=True):
    __tablename__ = "poll_options"

    poll: "Poll" = Relationship(back_populates="options")
