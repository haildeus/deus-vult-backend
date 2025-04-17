import logging

from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler
from pyrogram.types import InlineQuery

logger = logging.getLogger("deus-vult.telegram.inline")


class InlineHandlers:
    async def inline_query(self, _: Client, inline_query: InlineQuery) -> None:
        logger.info("Inline query: %s", inline_query)
        raise NotImplementedError()

    @property
    def inline_handlers(self) -> list[Handler]:
        return [
            InlineQueryHandler(self.inline_query, filters.group),
        ]
