from sqlmodel import Relationship, SQLModel

from src.now_the_game.telegram.chats.chats_schemas import ChatTable
from src.now_the_game.telegram.memberships.memberships_schemas import (
    ChatMembershipTable,
)
from src.now_the_game.telegram.messages.messages_schemas import MessageTable
from src.now_the_game.telegram.polls.polls_schemas import (
    PollOptionTable,
    PollTable,
)
from src.now_the_game.telegram.users.users_schemas import UserTable

"""
User relationships
"""
UserTable.chat_members = Relationship(
    back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
)
UserTable.messages = Relationship(
    back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
)
UserTable.chats = Relationship(
    back_populates="users",
    link_model=ChatMembershipTable,
    sa_relationship_kwargs={"lazy": "selectin"},
)
"""
Chat relationships
"""
ChatTable.chat_members = Relationship(
    back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
)
ChatTable.messages = Relationship(
    back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
)
ChatTable.polls = Relationship(
    back_populates="chat", sa_relationship_kwargs={"lazy": "selectin"}
)
ChatTable.users = Relationship(
    back_populates="chats",
    link_model=ChatMembershipTable,
    sa_relationship_kwargs={"lazy": "selectin"},
)

"""
ChatMembership relationships
"""
ChatMembershipTable.chat = Relationship(
    back_populates="chat_members", sa_relationship_kwargs={"lazy": "selectin"}
)
ChatMembershipTable.user = Relationship(
    back_populates="chat_members", sa_relationship_kwargs={"lazy": "selectin"}
)

"""
Message relationships
"""
MessageTable.chat = Relationship(
    back_populates="messages", sa_relationship_kwargs={"lazy": "selectin"}
)
MessageTable.user = Relationship(
    back_populates="messages", sa_relationship_kwargs={"lazy": "selectin"}
)
MessageTable.polls = Relationship(
    back_populates="message", sa_relationship_kwargs={"lazy": "selectin"}
)

"""
Poll relationships
"""
PollTable.options = Relationship(
    back_populates="poll", sa_relationship_kwargs={"lazy": "selectin"}
)
PollTable.message = Relationship(
    back_populates="polls", sa_relationship_kwargs={"lazy": "selectin"}
)
PollTable.chat = Relationship(
    back_populates="polls", sa_relationship_kwargs={"lazy": "selectin"}
)

"""
PollOption relationships
"""
PollOptionTable.poll = Relationship(
    back_populates="options", sa_relationship_kwargs={"lazy": "selectin"}
)


def get_telegram_registry():
    return SQLModel.metadata
