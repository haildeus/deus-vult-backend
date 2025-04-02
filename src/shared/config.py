import logging
from abc import ABC
from enum import Enum

from pydantic_settings import BaseSettings

"""
ABSTRACT BASE CONFIG CLASSES
"""


class BaseConfig(BaseSettings, ABC):
    """Abstract base class for configuration settings across vertical slices"""

    class Config:
        extra = "ignore"
        env_file = ".env"


class PostgresConfig(BaseConfig):
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: int = 5432

    class Config(BaseConfig.Config):
        env_prefix = "POSTGRES_"

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}"
        )


"""
SHARED CONFIG
"""


class EventBusType(Enum):
    LOCAL = "local"


class SharedConfig(BaseConfig):
    event_bus: EventBusType = EventBusType.LOCAL
    debug_mode: bool = True
    log_level: int = logging.DEBUG if debug_mode else logging.INFO

    class Config(BaseConfig.Config):
        env_prefix = "GLOBAL_"


shared_config = SharedConfig()
