"""Telegram handlers module"""

from pyrogram.handlers.handler import Handler

from src.now_the_game.telegram.memberships.memberships_handlers import (
    ChatMembershipHandlers,
)


class TelegramHandlers:
    """Telegram handlers class"""

    def __init__(self):
        self.chat_membership_handlers = ChatMembershipHandlers()

    @property
    def all_handlers(self) -> list[Handler]:
        return [
            *self.chat_membership_handlers.chat_membership_handlers,
        ]
