from pathlib import Path

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        extra = "ignore"
        env_file = ".env"
        env_prefix = "GLOBAL_"


class StorageConfig(BaseSettings):
    storage_path: Path = Path("src/now_the_game/storage")

    # SQLite config
    db_path: Path = storage_path / "database.db"
    schemas_path: Path = storage_path / "schemas"
    queries_path: Path = storage_path / "queries"

    # Chroma config
    chroma_in_memory: bool = True
    chroma_collection_default_name: str = "messages"

    class Config:
        extra = "ignore"
        env_file = ".env"
        env_prefix = "STORAGE_"


config = Config()
