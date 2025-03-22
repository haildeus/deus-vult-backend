from pyrogram import Client
from pyrogram.enums import ParseMode

from ... import logger
from .telegram_config import TelegramBotData, TelegramBotStatus, TelegramConfig


class TelegramBot:
    """Telegram bot client."""

    status: TelegramBotStatus = TelegramBotStatus.STOPPED

    def __init__(self, config: TelegramConfig) -> None:
        logger.info("Initializing Telegram bot with .env config")
        self.data = TelegramBotData()
        self.api_token = config.bot_token
        self.client = Client(
            name=config.bot_session_name,
            api_id=config.api_id,
            api_hash=config.api_hash,
            bot_token=config.bot_token,
            workdir=config.bot_session_dir,
        )
        logger.info("Client object initialized")

    async def _fill_session_data(self):
        await self.data.fill_from_client(self.client)
        logger.info("Filled session data")

    async def _setup_client(self):
        self.client.set_parse_mode(ParseMode.HTML)

    def get_status(self):
        return self.status

    def get_data(self):
        return self.data

    def get_client(self):
        return self.client

    def change_status(self, status: TelegramBotStatus):
        self.status = status
        logger.info(f"Client status: {self.status.value}")

    async def start(self):
        await self.client.start()
        logger.info("Client started")
        await self._fill_session_data()
        await self._setup_client()
        logger.info("Client setup complete")
        self.change_status(TelegramBotStatus.RUNNING)

    async def stop(self):
        await self.client.stop()
        self.change_status(TelegramBotStatus.STOPPED)
