from sqlmodel import MetaData, SQLModel

from src.api.users.users_schemas import UserTable  # type: ignore
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


async def get_telegram_registry() -> MetaData:
    return SQLModel.metadata
