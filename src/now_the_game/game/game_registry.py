from sqlmodel import Relationship, SQLModel

from .characters.characters_schemas import CharacterTable, LoreTable, PrimaryStatsTable
from .sessions.sessions_schemas import GameSessionTable


CharacterTable.lore = Relationship(back_populates="character")
CharacterTable.primary_stats = Relationship(back_populates="character")

LoreTable.character = Relationship(back_populates="lore")

PrimaryStatsTable.character = Relationship(back_populates="primary_stats")

GameSessionTable.chat = Relationship(back_populates="game_session")


def get_game_registry():
    return SQLModel.metadata
