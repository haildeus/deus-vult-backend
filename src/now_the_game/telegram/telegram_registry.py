from sqlmodel import SQLModel

from .telegram_schemas import *


def get_telegram_registry():
    return SQLModel.metadata
