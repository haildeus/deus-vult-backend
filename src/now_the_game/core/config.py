from enum import Enum

from pydantic_settings import BaseSettings


class EventBusType(Enum):
    LOCAL = "local"


class Config(BaseSettings):
    event_bus: EventBusType = EventBusType.LOCAL

    class Config:
        extra = "ignore"
        env_file = ".env"
        env_prefix = "GLOBAL_"


config = Config()
