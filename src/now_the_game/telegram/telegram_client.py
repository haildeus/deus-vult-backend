from dataclasses import dataclass
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings
from pyrogram import Client
from pyrogram.enums import ParseMode

from .. import logger
from .telegram_exceptions import MissingCredentialsError
from .telegram_schemas import TelegramBotStatus


class TelegramConfig(BaseSettings):
    """Settings for the Telegram bot."""

    # TELEGRAM ENVIRONMENT VARIABLES
    bot_token: str
    api_id: int
    api_hash: str

    # DEFAULT VALUES
    bot_session_dir: Path = Path("src/now_the_game/storage")
    bot_session_name: str = "bot_session"

    class Config:
        extra = "ignore"
        env_file = ".env"
        env_prefix = "TELEGRAM_"

    @model_validator(mode="before")
    def validate_base_fields(cls, values):
        if not values.get("bot_token"):
            raise MissingCredentialsError("bot_token must be provided")
        if not values.get("api_id"):
            raise MissingCredentialsError("api_id must be provided")
        if not values.get("api_hash"):
            raise MissingCredentialsError("api_hash must be provided")
        return values


@dataclass
class TelegramBotData:
    peer_id: int | None = None
    name: str | None = None
    username: str | None = None

    async def fill_from_client(self, client: Client):
        bot_info = await client.get_me()
        self.peer_id = bot_info.id
        self.name = bot_info.first_name
        self.username = bot_info.username
        logger.info(f"Bot info: {self}")


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
