"""
ChatMembership-specific schema definitions.
"""

from datetime import datetime
from enum import Enum

from pyrogram.client import Client
from pyrogram.types import ChatMember, ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from ... import logger
from ...core.base import BaseSchema
from ...core.events import EventPayload
from ..telegram_exceptions import PyrogramConversionError
from ..telegram_interfaces import IMembershipChanged

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "telegram.memberships"

"""
ENUMS
"""


class MembershipTopics(Enum):
    MEMBERSHIP_ADDED = f"{EVENT_BUS_PREFIX}.added"
    MEMBERSHIP_CHANGED = f"{EVENT_BUS_PREFIX}.changed"


"""
MODELS
"""


class AddChatMembershipPayload(EventPayload):
    client: Client
    message: Message
    db_session: AsyncSession


class ChangeChatMembershipPayload(EventPayload):
    client: Client
    chat_member_updated: ChatMemberUpdated
    updated_info: ChatMember
    db_session: AsyncSession
    new_member: bool


"""
EVENTS
"""


class ChangeChatMembershipEvent(IMembershipChanged):
    topic: str = MembershipTopics.MEMBERSHIP_CHANGED.value
    payload: ChangeChatMembershipPayload  # type: ignore


class AddChatMembershipEvent(IMembershipChanged):
    topic: str = MembershipTopics.MEMBERSHIP_ADDED.value
    payload: AddChatMembershipPayload  # type: ignore


"""
TABLES
"""


class ChatMembershipBase(BaseSchema):
    user_id: int = Field(foreign_key="users.object_id", primary_key=True)
    chat_id: int = Field(foreign_key="chats.object_id", primary_key=True)
    joined_at: datetime = Field(default=datetime.now())


class ChatMembershipTable(ChatMembershipBase, table=True):
    __tablename__ = "chat_members"  # type: ignore

    @classmethod
    async def create(cls, user_id: int, chat_id: int) -> "ChatMembershipTable":
        try:
            assert user_id is not None
            assert chat_id is not None
        except AssertionError as e:
            raise ValueError("User ID and chat ID must be provided") from e

        return cls(user_id=user_id, chat_id=chat_id)

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "ChatMembershipTable":
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
