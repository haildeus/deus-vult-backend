import logging
import random

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from pyrogram.errors.exceptions.forbidden_403 import UserNotParticipant
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import CallbackQuery

from src.now_the_game.telegram.callback.callback_utils import is_game_basic_keyboard
from src.now_the_game.telegram.content.content_path import WELCOME_MESSAGE_PATH
from src.now_the_game.telegram.text.art import ANGEL_ART
from src.now_the_game.telegram.text.keyboards import (
    GAME_BASIC_KEYBOARD,
    JOIN_THE_CRUSADE_KEYBOARD,
)
from src.now_the_game.telegram.text.messages import (
    CALLBACK_QUERY_PRIVATE_MESSAGES,
    CALLBACK_QUERY_USER_HAS_CHARACTER,
    INTRO_MESSAGE,
    NEW_CHARACTER_WELCOME_MESSAGE_1,
    NEW_CHARACTER_WELCOME_MESSAGE_2,
    NEW_CHARACTER_WELCOME_MESSAGE_3,
    NEW_CHARACTER_WELCOME_MESSAGE_4,
)

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
        if (
            callback_query.game_short_name is not None  # type: ignore
            and callback_query.game_short_name == "deusvult"
        ):
            is_basic_game_keyboard = is_game_basic_keyboard(callback_query)

            if is_basic_game_keyboard:
                user = callback_query.from_user.first_name

                # 1. Check if the user has its character created
                has_character = False  # TODO: Replace the placeholder
                # 2. If they have character, show notification
                if has_character:
                    await callback_query.answer(
                        text=CALLBACK_QUERY_USER_HAS_CHARACTER.format(user=user),
                        show_alert=True,
                        cache_time=10,
                    )
                # 3. If they don't have character, create a new character,
                # + send a welcome message
                else:
                    # TODO: create a new character

                    chosen_message = random.choice(
                        [
                            NEW_CHARACTER_WELCOME_MESSAGE_1,
                            NEW_CHARACTER_WELCOME_MESSAGE_2,
                            NEW_CHARACTER_WELCOME_MESSAGE_3,
                            NEW_CHARACTER_WELCOME_MESSAGE_4,
                        ]
                    )

                    await callback_query.message.reply_photo(  # type: ignore
                        photo=WELCOME_MESSAGE_PATH,
                        caption=chosen_message.format(user=user),
                        quote=False,
                    )
            else:
                # Transform the message to the default game keyboard
                inline_message_id = callback_query.inline_message_id
                user = callback_query.from_user.first_name

                await callback_query.answer(
                    text=CALLBACK_QUERY_PRIVATE_MESSAGES.format(user=user),
                    show_alert=True,
                    cache_time=10,
                )
                try:
                    await client.edit_inline_reply_markup(
                        inline_message_id=inline_message_id,
                        reply_markup=GAME_BASIC_KEYBOARD,
                    )
                except MessageNotModified:
                    pass
                except Exception as e:
                    logger.error("Error editing inline reply markup: %s", e)
                    pass

        elif callback_query.data == "launch_game":
            # 1. Send a message to the user
            # 2. Send the game setup
            # 3. Delete the initial message

            await client.send_message(
                callback_query.message.chat.id,
                text=f"{ANGEL_ART}\n\n{INTRO_MESSAGE}",
                reply_markup=JOIN_THE_CRUSADE_KEYBOARD,
            )
            await client.send_game(
                callback_query.message.chat.id,
                "deusvult",
                reply_markup=GAME_BASIC_KEYBOARD,
            )

            # await callback_query.message.delete()
        else:
            await client.answer_callback_query(
                callback_query.id,
                text="Invalid option, sorry!",
                show_alert=True,
                cache_time=10,
            )

    @property
    def callback_handlers(self) -> list[Handler]:
        is_bot_in_chat = filters.create(CallbackHandlers.is_bot_in_chat)  # type: ignore
        is_user_in_chat = filters.create(CallbackHandlers.is_user_in_chat)  # type: ignore

        return [
            # # Handle callback queries when bot is not in chat
            # CallbackQueryHandler(
            #     CallbackHandlers.on_callback_when_bot_not_in_chat,
            #     ~is_bot_in_chat,
            # ),
            # # Handle callback queries when user is not in chat
            # CallbackQueryHandler(
            #     CallbackHandlers.on_callback_when_user_not_in_chat,
            #     ~is_user_in_chat,
            # ),
            # Handle callback queries in groups
            CallbackQueryHandler(
                CallbackHandlers.on_callback_query,  # is_bot_in_chat & is_user_in_chat
            ),
        ]
