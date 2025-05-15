from pyrogram.types import (
    CallbackGame,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.now_the_game.telegram.text.buttons import (
    GAME_BASIC_BUTTON_1,
    GAME_BASIC_BUTTON_2,
    JOIN_THE_CRUSADE_PLACEHOLDER,
    JOIN_THE_CRUSADE_REPLY_1,
    JOIN_THE_CRUSADE_REPLY_2,
)

JOIN_THE_CRUSADE_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text=JOIN_THE_CRUSADE_REPLY_1,
            ),
            KeyboardButton(
                text=JOIN_THE_CRUSADE_REPLY_2,
            ),
        ]
    ],
    resize_keyboard=False,
    one_time_keyboard=True,
    placeholder=JOIN_THE_CRUSADE_PLACEHOLDER,
)

GAME_BASIC_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text=GAME_BASIC_BUTTON_1,
                callback_game=CallbackGame(),
            ),
            InlineKeyboardButton(
                text=GAME_BASIC_BUTTON_2,
                url="t.me/infinitecrafttestbot/infinitecrafttest",
            ),
        ]
    ]
)
