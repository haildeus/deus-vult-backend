from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler
from pyrogram.types import InlineQuery

from src.now_the_game import logger


class InlineHandlers:
    def __init__(self, client: Client):
        self.client = client

    async def inline_query(self, client: Client, inline_query: InlineQuery) -> None:
        logger.info(f"Inline query: {inline_query}")
        raise NotImplementedError()

    @property
    def inline_handlers(self) -> list[Handler]:
        return [
            InlineQueryHandler(self.inline_query, filters.group),
        ]
