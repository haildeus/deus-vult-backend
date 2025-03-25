"""Telegram handlers module"""

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.filters import Filter
from pyrogram.handlers.chat_member_updated_handler import ChatMemberUpdatedHandler
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.types import ChatMemberUpdated, Message, Update

from .. import logger
from .telegram_orchestrator import telegram_orchestrator


class CustomFilters:
    async def participating_chat(self, client: Client, update: Update) -> bool:
        return True

    @property
    def participating_chat_filter(self) -> Filter:
        return filters.create(func=self.participating_chat, name="participating_chat")  # type: ignore


class MessageHandlers:
    """
    Message handlers class
    """

    def __init__(self):
        self.custom_filters = CustomFilters()

    async def start_message(self, client: Client, message: Message) -> Message:
        response = await message.reply_text("Hello, world!")  # type: ignore
        return response

    async def help_message(self, client: Client, message: Message) -> Message:
        response = await message.reply_text("Help message")  # type: ignore
        return response

    async def save(self, client: Client, message: Message) -> Message:
        """
        Process a message from Telegram and add it to the database.
        """
        logger.debug(f"Processing message: {message.id}")
        await telegram_orchestrator.new_message(message)
        response = await message.reply_text("Message processed")  # type: ignore
        return response

    @property
    def message_handlers(self) -> list[Handler]:
        return [
            MessageHandler(self.start_message, filters.command("start")),
            MessageHandler(self.help_message, filters.command("help")),
            MessageHandler(
                self.save,
                filters.group
                & filters.incoming
                & self.custom_filters.participating_chat_filter
                & ~filters.service,
            ),
        ]


class ChatMembershipHandlers:
    """
    Chat membership handlers class
    """

    async def new_chat_membership(
        self, client: Client, chat_member_updated: ChatMemberUpdated
    ) -> None:
        """
        Process a new chat membership event and add it to the database.
        """

        logger.debug(f"Processing chat membership: {chat_member_updated.chat.id}")
        new_member = True if chat_member_updated.new_chat_member else False
        logger.debug(f"Member is new: {new_member}")

        await telegram_orchestrator.new_chat_member(
            client, chat_member_updated, new_member
        )

        if new_member:
            await client.send_message(chat_member_updated.chat.id, "Hi!")

    @property
    def chat_membership_handlers(self) -> list[Handler]:
        return [
            ChatMemberUpdatedHandler(self.new_chat_membership, filters.group),
        ]


class TelegramHandlers:
    """Telegram handlers class"""

    def __init__(self):
        self.message_handlers = MessageHandlers()
        self.chat_membership_handlers = ChatMembershipHandlers()

    async def get_all_handlers(self) -> list[Handler]:
        return [
            *self.message_handlers.message_handlers,
            *self.chat_membership_handlers.chat_membership_handlers,
        ]
