from typing import Any

from pydantic import model_validator

from src.shared.base import MissingCredentialsError
from src.shared.config import BaseConfig


class ApiConfig(BaseConfig):
    bot_token: str | None = None

    class Config(BaseConfig.Config):
        env_prefix = "TELEGRAM_"

    @model_validator(mode="before")
    def validate_base_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("bot_token"):
            raise MissingCredentialsError("bot_token must be provided")
        return values


api_config = ApiConfig()
