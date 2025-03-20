from enum import Enum


class TelegramBotStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"
