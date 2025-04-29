"""Telegram handlers module"""

from pyrogram.handlers.handler import Handler

from src.now_the_game.telegram.callback.callback_handlers import CallbackHandlers
from src.now_the_game.telegram.memberships.memberships_handlers import (
    ChatMembershipHandlers,
)


class TelegramHandlers:
    """Telegram handlers class"""

    def __init__(self) -> None:
        self.chat_membership_handlers = ChatMembershipHandlers()
        self.callback_handlers = CallbackHandlers()

    @property
    def all_handlers(self) -> list[Handler]:
        return [
            *self.chat_membership_handlers.chat_membership_handlers,
            *self.callback_handlers.callback_handlers,
        ]
