from sqlmodel import SQLModel

from src.now_the_game.telegram.chats.chats_schemas import ChatTable  # type: ignore
from src.now_the_game.telegram.memberships.memberships_schemas import (
    ChatMembershipTable,  # type: ignore
)
from src.now_the_game.telegram.messages.messages_schemas import (
    MessageTable,  # type: ignore
)
from src.now_the_game.telegram.polls.polls_schemas import (
    PollOptionTable,  # type: ignore
    PollTable,  # type: ignore
)
from src.now_the_game.telegram.users.users_schemas import UserTable  # type: ignore


async def get_telegram_registry():
    return SQLModel.metadata
