from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from src.now_the_game.telegram.text.buttons import (
    GAME_BASIC_BUTTON_1,
    GAME_BASIC_BUTTON_2,
)


def is_game_basic_keyboard(query: CallbackQuery) -> bool:
    try:
        assert query.message is not None
        assert query.message.reply_markup is not None
        assert isinstance(query.message.reply_markup, InlineKeyboardMarkup)
        keyboard_list = query.message.reply_markup.inline_keyboard
        assert len(keyboard_list) == 1
        first_row = keyboard_list[0]
        assert len(first_row) == 2
        assert first_row[0].text == GAME_BASIC_BUTTON_1
        assert first_row[1].text == GAME_BASIC_BUTTON_2
        return True
    except AssertionError:
        return False
