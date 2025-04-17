import logging
from datetime import datetime
from typing import cast

from pyrogram.client import Client
from pyrogram.types import Message

from src.now_the_game.telegram.messages.messages_model import message_model
from src.now_the_game.telegram.messages.messages_schemas import (
    AddMessagePayload,
    MessageTable,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import MessageTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.telegram.messages")


class MessagesService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self.message_model = message_model

    @EventBus.subscribe(MessageTopics.MESSAGE_CREATE)
    @async_traced_function
    async def on_add_message(self, event: Event) -> None:
        payload = cast(
            AddMessagePayload,
            event.extract_payload(event, AddMessagePayload),
        )

        logger.debug("Processing new message: %s", payload.message.text)
        message_core_info = await MessageTable.from_pyrogram(payload.message)

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            await self.message_model.add(db, message_core_info)
            logger.debug("Message added: %s", message_core_info)
        else:
            logger.debug("No active uow, skipping")

    @async_traced_function
    async def get_messages(
        self, chat_id: int | str, message_ids: list[int] | int, client: Client
    ) -> list[Message] | Message | None:
        message_request = await client.get_messages(
            chat_id=chat_id,
            message_ids=message_ids,
        )
        return message_request

    @async_traced_function
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

    @async_traced_function
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
            caption=caption or '',
            schedule_date=schedule,  # type: ignore
            ttl_seconds=ttl_seconds,  # type: ignore
        )
        return photo_message

    @async_traced_function
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

    @async_traced_function
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
