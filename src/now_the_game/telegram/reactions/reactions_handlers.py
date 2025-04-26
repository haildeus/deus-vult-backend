import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from dependency_injector.wiring import Provide, inject
from pyrogram import filters
from pyrogram.handlers.handler import Handler
from pyrogram.handlers.message_handler import MessageHandler

logger = logging.getLogger("deus-vult.telegram.reactions")


class ReactionsHandlers:
    """
    Reactions handlers class
    """
