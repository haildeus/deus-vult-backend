import logging

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import CallbackQuery

logger = logging.getLogger("deus-vult.telegram.callback")


class CallbackHandlers:
    def __init__(self) -> None:
        pass

    async def callback_query(
        self, client: Client, callback_query: CallbackQuery
    ) -> None:
        raise NotImplementedError()

    @property
    def inline_handlers(self) -> list[Handler]:
        return [
            CallbackQueryHandler(self.callback_query, filters.group),
        ]
