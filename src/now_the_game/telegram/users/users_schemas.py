"""
User-specific schema definitions.
This module re-exports the User-related schemas from the central schema module.
"""

from enum import Enum
from typing import Any

from pyrogram.client import Client
from pyrogram.types import Message, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from src import BaseSchema, EventPayload
from src.now_the_game.telegram.telegram_interfaces import IUserEvent

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "telegram.users"

"""
ENUMS
"""


class UserTopics(Enum):
    USER_ADDED = f"{EVENT_BUS_PREFIX}.added"


"""
MODELS
"""


class AddUserPayload(EventPayload):
    client: Client
    user: User
    db_session: AsyncSession


"""
EVENTS
"""


class AddUserEvent(IUserEvent):
    topic: str = UserTopics.USER_ADDED.value
    payload: AddUserPayload  # type: ignore


"""
TABLES
"""


class UserBase(BaseSchema):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    username: str | None = Field(default=None, min_length=1, max_length=100)
    is_premium: bool = Field(default=False)
    bio: str | None = Field(default=None, min_length=1, max_length=255)
    photo_url: str | None = Field(default=None, min_length=1, max_length=255)


class UserTable(UserBase, table=True):
    __tablename__ = "users"  # type: ignore

    @classmethod
    async def from_fields(cls, **kwargs: Any) -> "UserTable":
        """Create a user from a dictionary of fields"""
        try:
            assert "object_id" in kwargs
            assert "first_name" in kwargs
            assert "is_premium" in kwargs
        except AssertionError as e:
            raise ValueError("Missing required fields") from e

        return cls(
            object_id=kwargs.get("object_id", 0),
            first_name=kwargs.get("first_name", ""),
            last_name=kwargs.get("last_name", None),
            username=kwargs.get("username", None),
            is_premium=kwargs.get("is_premium", False),
            bio=kwargs.get("bio", None),
            photo_url=kwargs.get("photo_url", None),
        )

    @classmethod
    async def from_user(cls, user: User) -> "UserTable":
        return cls(
            object_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            is_premium=user.is_premium,
        )

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "UserTable":
        """Create a user from a pyrogram message"""

        return cls(
            object_id=message.from_user.id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            username=message.from_user.username,
            is_premium=message.from_user.is_premium,
        )
