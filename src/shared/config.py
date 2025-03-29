import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings

"""
ABSTRACT BASE CONFIG CLASSES
"""


class BaseConfig(BaseSettings, ABC):
    """Abstract base class for configuration settings across vertical slices"""

    class Config:
        extra = "ignore"
        env_file = ".env"


class BaseStorageConfig(BaseConfig, ABC):
    """Abstract base class for storage configuration settings"""

    @property
    @abstractmethod
    def storage_path(self) -> Path:
        """Storage path"""
        pass

    @property
    @abstractmethod
    def db_path(self) -> Path:
        """Database path"""
        pass


"""
SHARED CONFIG
"""


class EventBusType(Enum):
    LOCAL = "local"


class SharedConfig(BaseConfig):
    event_bus: EventBusType = EventBusType.LOCAL
    log_level: int = logging.DEBUG

    class Config(BaseConfig.Config):
        env_prefix = "GLOBAL_"


shared_config = SharedConfig()
