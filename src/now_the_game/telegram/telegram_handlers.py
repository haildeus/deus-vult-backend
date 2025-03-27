"""Telegram handlers module"""

from pyrogram.handlers.handler import Handler

from src.now_the_game.telegram.memberships.memberships_handlers import (
    ChatMembershipHandlers,
)
from src.now_the_game.telegram.messages.messages_handlers import MessageHandlers


class TelegramHandlers:
    """Telegram handlers class"""

    def __init__(self):
        self.message_handlers = MessageHandlers()
        self.chat_membership_handlers = ChatMembershipHandlers()

    def get_all_handlers(self) -> list[Handler]:
        return [
            *self.message_handlers.message_handlers,
            *self.chat_membership_handlers.chat_membership_handlers,
        ]
