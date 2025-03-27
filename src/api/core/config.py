from pathlib import Path
from typing import Any

from pydantic import model_validator

from src import BaseConfig, BaseStorageConfig, MissingCredentialsError


class ApiConfig(BaseConfig):
    bot_token: str | None = None

    class Config(BaseConfig.Config):
        env_prefix = "TELEGRAM_"

    @model_validator(mode="before")
    def validate_base_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("bot_token"):
            raise MissingCredentialsError("bot_token must be provided")
        return values


class ApiStorageConfig(BaseStorageConfig):
    @property
    def storage_path(self) -> Path:
        return Path("src/api/storage")

    @property
    def db_path(self) -> Path:
        return self.storage_path / "database.db"

    class Config(BaseStorageConfig.Config):
        env_prefix = "MINIAPPS_BACKEND_"


api_storage_config = ApiStorageConfig()
api_config = ApiConfig()
