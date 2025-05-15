import logging
from typing import cast

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
