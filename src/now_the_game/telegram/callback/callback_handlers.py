from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import CallbackQuery

from src import Event, event_bus
from src.now_the_game import db, logger


class CallbackHandlers:
    def __init__(self, client: Client):
        self.client = client

    async def callback_query(
        self, client: Client, callback_query: CallbackQuery
    ) -> None:
        logger.info(f"Callback query: {callback_query}")
        raise NotImplementedError()

    @property
    def inline_handlers(self) -> list[Handler]:
        return [
            CallbackQueryHandler(self.callback_query, filters.group),
        ]
