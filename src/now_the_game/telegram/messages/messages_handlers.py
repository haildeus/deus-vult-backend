import asyncio

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import Message

from src import Event, event_bus
from src.now_the_game import db, logger


class MessageHandlers:
    """
    Message handlers class
    """

    async def start_message(self, client: Client, message: Message) -> Message:
        response = await message.reply_text("Hello, world!")  # type: ignore
        return response

    async def help_message(self, client: Client, message: Message) -> Message:
        response = await message.reply_text("Help message")  # type: ignore
        return response

    async def save(self, client: Client, message: Message) -> None:
        """
        Process a new message event and add it to the database.
        """
        logger.debug(f"Processing new message: {message.text}")

        async with db.session() as session:
            pyrogram_payload = {
                "client": client,
                "message": message,
                "db_session": session,
            }
            add_message_event = Event(
                topic="telegram.messages.added",
                payload=pyrogram_payload,
            )

            add_chat_event = Event(
                topic="telegram.chats.added",
                payload=pyrogram_payload,
            )

            add_user_event = Event(
                topic="telegram.users.added",
                payload=pyrogram_payload,
            )

            add_membership_event = Event(
                topic="telegram.memberships.added",
                payload=pyrogram_payload,
            )

            await asyncio.gather(
                event_bus.publish_and_wait(add_message_event),
                event_bus.publish_and_wait(add_chat_event),
                event_bus.publish_and_wait(add_user_event),
                event_bus.publish_and_wait(add_membership_event),
            )

            await session.flush()
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
