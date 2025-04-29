import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from dependency_injector.wiring import Provide, inject
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message

from src import Container
from src.shared.event_bus import EventBus
from src.shared.event_registry import (
    ChatTopics,
    MembershipTopics,
    MessageTopics,
    UserTopics,
)
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork

logger = logging.getLogger("deus-vult.telegram.messages")


class MessageHandlers:
    """
    Message handlers class
    """

    @staticmethod
    async def start_message(_: Client, message: Message) -> Message:
        response = await message.reply_text("Hello, world!")  # type: ignore
        return response

    @staticmethod
    async def help_message(_: Client, message: Message) -> Message:
        response = await message.reply_text("Help message")  # type: ignore
        return response

    @async_traced_function
    @inject
    async def save(
        self,
        _: Client,
        message: Message,
        uow_factory: Callable[[], UnitOfWork] = Provide[Container.uow_factory],
        event_bus: EventBus = Provide[Container.event_bus],
    ) -> None:
        """
        Process a new message event and add it to the database.
        """
        logger.debug("Processing new message: %s", message.text)
        uow = uow_factory()

        async with uow.start():
            session = await uow.get_session()

            pyrogram_payload = {
                "message": message,
                "db_session": session,
            }

            message_array = [
                MessageTopics.MESSAGE_CREATE.value,
                ChatTopics.CHAT_CREATE.value,
                UserTopics.USER_CREATE_FROM_TELEGRAM.value,
                MembershipTopics.MEMBERSHIP_CREATE.value,
            ]
            async_tasks: list[Coroutine[Any, Any, None]] = []

            for topic in message_array:
                event = Event.from_dict(topic, pyrogram_payload)
                async_tasks.append(event_bus.publish_and_wait(event))
            await asyncio.gather(*async_tasks)
            logger.debug("All events published")

    @property
    def message_handlers(self) -> list[Handler]:
        return [
            MessageHandler(self.start_message, filters.command("start")),
            MessageHandler(self.help_message, filters.command("help")),
            MessageHandler(
                self.save,
                filters.group & filters.incoming & ~filters.service,
            ),
            MessageHandler(self.save, filters.private & filters.incoming),
        ]
