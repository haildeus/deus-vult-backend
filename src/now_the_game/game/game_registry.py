from sqlmodel import SQLModel

from .characters.characters_schemas import *
from .sessions.sessions_schemas import *


def get_game_registry():
    return SQLModel.metadata
