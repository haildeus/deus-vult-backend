from pyrogram.client import Client
from pyrogram.types import Chat

from ... import event_bus, logger
from ...core.events import Event
from .users_model import user_model
from .users_schemas import AddUserEvent, AddUserPayload, UserTable


class UsersService:
    def __init__(self, client: Client):
        self.client = client
        self.model = user_model
        self.event_bus = event_bus

        # Subscribe to events
        self.event_bus.subscribe_to_topic(AddUserEvent, self.on_add_user)

    async def on_add_user(self, event: Event) -> None:
        if not isinstance(event.payload, AddUserPayload):
            payload = AddUserPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        user = payload.user
        user_core_info = await UserTable.from_user(user)
        db = payload.db_session
        logger.debug(f"Adding user: {user_core_info}")
        await self.model.add(db, user_core_info)

    async def get(
        self,
        chat_id: int | str,
    ) -> Chat:
        chat_request = await self.client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

    async def get_photos_count(
        self,
        chat_id: int | str,
    ) -> int:
        chat_photos_count_request = await self.client.get_chat_photos_count(
            chat_id=chat_id,
        )
        return chat_photos_count_request
