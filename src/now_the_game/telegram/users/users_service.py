from pyrogram.client import Client
from pyrogram.types import Chat

from src.now_the_game import logger, logger_wrapper
from src.now_the_game.telegram.users.users_model import user_model
from src.now_the_game.telegram.users.users_schemas import (
    AddUserPayload,
    UserTable,
    UserTopics,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class UsersService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = user_model

    @EventBus.subscribe(UserTopics.USER_CREATE.value)
    @logger_wrapper.log_debug
    async def on_add_user(self, event: Event) -> None:
        if not isinstance(event.payload, AddUserPayload):
            payload = AddUserPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        user = payload.user
        user_core_info = await UserTable.from_user(user)

        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            logger.debug(f"Adding user: {user_core_info}")
            await self.model.add(db, user_core_info)
        else:
            logger.debug("No active uow, skipping")

    async def get(
        self,
        client: Client,
        chat_id: int | str,
    ) -> Chat:
        chat_request = await client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

    async def get_photos_count(
        self,
        client: Client,
        chat_id: int | str,
    ) -> int:
        chat_photos_count_request = await client.get_chat_photos_count(
            chat_id=chat_id,
        )
        return chat_photos_count_request
