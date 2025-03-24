"""
This module exists to resolve circular imports between schema definitions.
All schema classes are imported and re-exported from this central location.
"""

from sqlmodel import Relationship

from .chats.chats_schemas import ChatBase
from .membership.membership_schemas import ChatMembershipBase
from .messages.messages_schemas import MessageBase
from .polls.polls_schemas import PollBase, PollOptionsBase
from .users.users_schemas import UserBase


class UserTable(UserBase, table=True):
    __tablename__ = "users"  # type: ignore

    # Relationships
    chat_members: list["ChatMembershipTable"] = Relationship(back_populates="user")
    messages: list["MessageTable"] = Relationship(back_populates="user")

    # A user must be associated with at least one chat
    chats: list["ChatTable"] = Relationship(
        back_populates="users", link_model=ChatMembershipBase
    )


class ChatTable(ChatBase, table=True):
    __tablename__ = "chats"  # type: ignore

    # Relationships
    chat_members: list["ChatMembershipTable"] = Relationship(back_populates="chat")
    messages: list["MessageTable"] = Relationship(back_populates="chat")
    polls: list["PollTable"] = Relationship(back_populates="chat")

    # Users in this chat
    users: list["UserTable"] = Relationship(
        back_populates="chats", link_model=ChatMembershipBase
    )


class ChatMembershipTable(ChatMembershipBase, table=True):
    __tablename__ = "chat_members"  # type: ignore

    chat: ChatTable = Relationship(back_populates="chat_members")
    user: UserTable = Relationship(back_populates="chat_members")


class MessageTable(MessageBase, table=True):
    __tablename__ = "messages"  # type: ignore

    chat: ChatTable = Relationship(back_populates="messages")
    user: UserTable = Relationship(back_populates="messages")
    polls: list["PollTable"] = Relationship(back_populates="message")


class PollTable(PollBase, table=True):
    __tablename__ = "polls"  # type: ignore

    options: list["PollOptionTable"] = Relationship(back_populates="poll")
    message: MessageTable = Relationship(back_populates="polls")
    chat: ChatTable = Relationship(back_populates="polls")


class PollOptionTable(PollOptionsBase, table=True):
    __tablename__ = "poll_options"  # type: ignore

    poll: PollTable = Relationship(back_populates="options")
