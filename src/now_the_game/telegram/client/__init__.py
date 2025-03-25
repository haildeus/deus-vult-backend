"""
Telegram client module initialization
"""

from .client_object import TelegramBot
from .client_config import TelegramConfig
from .client_model import telegram

__all__ = ["TelegramBot", "TelegramConfig", "telegram"]
