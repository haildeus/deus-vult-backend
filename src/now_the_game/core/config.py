from pathlib import Path

from src import BaseStorageConfig


class StorageConfig(BaseStorageConfig):
    @property
    def storage_path(self) -> Path:
        return Path("src/now_the_game/storage")

    @property
    def db_path(self) -> Path:
        return self.storage_path / "database.db"

    class Config(BaseStorageConfig.Config):
        extra = "ignore"
        env_file = ".env"
        env_prefix = "STORAGE_"


storage_config = StorageConfig()
