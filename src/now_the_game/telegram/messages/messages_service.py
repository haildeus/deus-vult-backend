from datetime import datetime

from pyrogram.client import Client
from pyrogram.types import Message

from src.now_the_game import logger, logger_wrapper
from src.now_the_game.telegram.messages.messages_model import message_model
from src.now_the_game.telegram.messages.messages_schemas import (
    AddMessagePayload,
    MessageTable,
    MessageTopics,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class MessagesService(BaseService):
    def __init__(self):
        super().__init__()
        self.message_model = message_model

    @EventBus.subscribe(MessageTopics.MESSAGE_CREATE.value)
    @logger_wrapper.log_debug
    async def on_add_message(self, event: Event) -> None:
        if not isinstance(event.payload, AddMessagePayload):
            payload = AddMessagePayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Processing new message: {payload.message.text}")
        message_core_info = await MessageTable.from_pyrogram(payload.message)

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            await self.message_model.add(db, message_core_info)
            logger.debug(f"Message added: {message_core_info}")
        else:
            logger.debug("No active uow, skipping")

    async def get_messages(
        self, chat_id: int | str, message_ids: list[int] | int, client: Client
    ) -> list[Message] | Message | None:
        message_request = await client.get_messages(
            chat_id=chat_id,
            message_ids=message_ids,
        )
        return message_request

    async def send_message(
        self,
        client: Client,
        chat_id: int | str,
        text: str,
    ) -> Message:
        message = await client.send_message(
            chat_id=chat_id,
            text=text,
        )
        return message

    async def send_photo(
        self,
        client: Client,
        chat_id: int | str,
        photo: str,
        caption: str | None = None,
        schedule: datetime | None = None,
        ttl_seconds: int | None = None,
    ) -> Message | None:
        photo_message = await client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            schedule_date=schedule,
            ttl_seconds=ttl_seconds,
        )
        return photo_message

    async def send_game(
        self,
        client: Client,
        chat_id: int | str,
        game_short_name: str,
    ) -> Message:
        game_message = await client.send_game(
            chat_id=chat_id,
            game_short_name=game_short_name,
        )
        return game_message

    async def set_game_score(
        self,
        client: Client,
        chat_id: int | str,
        message_id: int,
        user_id: int | str,
        score: int,
        force: bool = False,
    ) -> Message | bool:
        set_game_score_message = await client.set_game_score(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            score=score,
            force=force,
        )
        return set_game_score_message
