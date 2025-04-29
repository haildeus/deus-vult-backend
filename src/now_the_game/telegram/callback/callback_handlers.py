import logging

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.errors.exceptions.forbidden_403 import UserNotParticipant
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import CallbackQuery

logger = logging.getLogger("deus-vult.telegram.callback")


class CallbackHandlers:
    @staticmethod
    async def is_bot_in_chat(_, client: Client, callback_query: CallbackQuery) -> bool:
        try:
            await client.get_chat_member(callback_query.message.chat.id, "me")
            return True

        except ChannelPrivate:
            logger.debug("Bot is not in chat: %s", callback_query.message.chat.id)
            return False
        except Exception as e:
            logger.error("Error getting chat member: %s", e)
            return False

    @staticmethod
    async def is_user_in_chat(_, client: Client, callback_query: CallbackQuery) -> bool:
        try:
            await client.get_chat_member(
                callback_query.message.chat.id, callback_query.from_user.id
            )
            return True
        except UserNotParticipant:
            logger.debug("User is not in chat: %s", callback_query.message.chat.id)
            return False
        except Exception as e:
            logger.error("Error getting chat member: %s", e)
            return False

    @staticmethod
    async def on_callback_when_bot_not_in_chat(
        client: Client,
        callback_query: CallbackQuery,
    ) -> None:
        await client.answer_callback_query(
            callback_query.id,
            text="Please, add @now_tgbot to the chat to play the game",
            show_alert=True,
            cache_time=120,
        )

    @staticmethod
    async def on_callback_when_user_not_in_chat(
        client: Client,
        callback_query: CallbackQuery,
    ) -> None:
        await client.answer_callback_query(
            callback_query.id,
            text="Join the group to play the game!",
            show_alert=True,
            cache_time=10,
        )

    @staticmethod
    async def on_callback_query(client: Client, callback_query: CallbackQuery) -> None:
        await client.answer_callback_query(
            callback_query.id,
            text="The game is about to start...",
            show_alert=True,
            cache_time=30,
        )

    @property
    def callback_handlers(self) -> list[Handler]:
        is_bot_in_chat = filters.create(CallbackHandlers.is_bot_in_chat)  # type: ignore
        is_user_in_chat = filters.create(CallbackHandlers.is_user_in_chat)  # type: ignore

        return [
            # Handle callback queries when bot is not in chat
            CallbackQueryHandler(
                CallbackHandlers.on_callback_when_bot_not_in_chat,
                ~is_bot_in_chat,
            ),
            # Handle callback queries when user is not in chat
            CallbackQueryHandler(
                CallbackHandlers.on_callback_when_user_not_in_chat,
                ~is_user_in_chat,
            ),
            # Handle callback queries in groups
            CallbackQueryHandler(
                CallbackHandlers.on_callback_query, is_bot_in_chat & is_user_in_chat
            ),
        ]
