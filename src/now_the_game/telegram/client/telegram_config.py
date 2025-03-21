from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings
from pyrogram import Client

from ... import logger
from ...core.base import MissingCredentialsError


class TelegramBotStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


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
