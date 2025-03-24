"""
User-specific schema definitions.
This module re-exports the User-related schemas from the central schema module.
"""

from pyrogram.types import Message
from sqlmodel import Field

from ...core.base import BaseSchema


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
