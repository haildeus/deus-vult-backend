from datetime import datetime

from pyrogram.client import Client
from pyrogram.types import Message

from src import BaseService, Event, event_bus
from src.now_the_game import logger
from src.now_the_game.telegram.messages.messages_model import message_model
from src.now_the_game.telegram.messages.messages_schemas import (
    AddMessagePayload,
    MessageTable,
    MessageTopics,
)


class MessagesService(BaseService):
    def __init__(self, client: Client):
        super().__init__()
        self.client = client
        self.message_model = message_model

    @event_bus.subscribe(MessageTopics.MESSAGE_CREATE.value)
    async def on_add_message(self, event: Event) -> None:
        if not isinstance(event.payload, AddMessagePayload):
            payload = AddMessagePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Processing new message: {payload.message.text}")
        message_core_info = await MessageTable.from_pyrogram(payload.message)
        await self.message_model.add(payload.db_session, message_core_info)
        logger.debug(f"Message added: {message_core_info}")

    async def get_messages(
        self,
        chat_id: int | str,
        message_ids: list[int] | int,
    ) -> list[Message] | Message | None:
        message_request = await self.client.get_messages(
            chat_id=chat_id,
            message_ids=message_ids,
        )
        return message_request

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        schedule: datetime | None = None,
    ) -> Message:
        message = await self.client.send_message(
            chat_id=chat_id,
            text=text,
            schedule_date=schedule,
        )
        return message

    async def send_photo(
        self,
        chat_id: int | str,
        photo: str,
        caption: str | None = None,
        schedule: datetime | None = None,
        ttl_seconds: int | None = None,
    ) -> Message:
        photo_message = await self.client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            schedule_date=schedule,
            ttl_seconds=ttl_seconds,
        )
        return photo_message

    async def send_game(
        self,
        chat_id: int | str,
        game_short_name: str,
    ) -> Message:
        game_message = await self.client.send_game(
            chat_id=chat_id,
            game_short_name=game_short_name,
        )
        return game_message

    async def set_game_score(
        self,
        chat_id: int | str,
        message_id: int,
        user_id: int | str,
        score: int,
        force: bool = False,
    ) -> Message:
        set_game_score_message = await self.client.set_game_score(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            score=score,
            force=force,
        )
        return set_game_score_message
