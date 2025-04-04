from pyrogram.client import Client
from pyrogram.enums import ParseMode
from pyrogram.handlers.handler import Handler
from pyrogram.methods.utilities.idle import idle

from src.now_the_game import logger
from src.now_the_game.telegram.client.client_config import (
    TelegramBotData,
    TelegramBotStatus,
    TelegramConfig,
)


class TelegramBot:
    """Telegram bot client."""

    status: TelegramBotStatus = TelegramBotStatus.STOPPED

    def __init__(
        self,
        config: TelegramConfig,
    ) -> None:
        logger.debug("Initializing Telegram bot with .env config")
        self.data = TelegramBotData()
        self.api_token = config.bot_token
        self.client = Client(
            name=config.bot_session_name,
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_token=config.bot_token,
            workdir=config.bot_session_dir,
        )
        logger.debug("Client object initialized")

    async def _fill_session_data(self):
        await self.data.fill_from_client(self.client)
        logger.debug("Filled session data")

    async def _setup_client(self):
        self.client.set_parse_mode(ParseMode.HTML)

    def get_status(self):
        return self.status

    def get_data(self):
        return self.data

    def get_client(self) -> Client:
        return self.client

    def change_status(self, status: TelegramBotStatus):
        self.status = status
        logger.debug(f"Client status: {self.status.value}")

    async def register_handlers(self, handlers: list[Handler]):
        for handler in handlers:
            logger.debug(f"Adding handler: {handler}")
            self.client.add_handler(handler)

    async def start(
        self, blocking: bool = False, handlers: list[Handler] | None = None
    ):
        await self.client.start()
        logger.debug("Client started")
        await self._fill_session_data()
        await self._setup_client()
        logger.debug("Client setup complete")
        self.change_status(TelegramBotStatus.RUNNING)

        if handlers:
            await self.register_handlers(handlers)

        if blocking:
            await idle()
            await self.client.stop()

    async def stop(self):
        await self.client.stop()
        self.change_status(TelegramBotStatus.STOPPED)
