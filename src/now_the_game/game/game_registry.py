from sqlmodel import Relationship, SQLModel

from src.now_the_game.game.characters.characters_schemas import (
    CharacterTable,
    LoreTable,
    PrimaryStatsTable,
)
from src.now_the_game.game.sessions.sessions_schemas import SessionTable

CharacterTable.lore = Relationship(back_populates="character")
CharacterTable.primary_stats = Relationship(back_populates="character")

LoreTable.character = Relationship(back_populates="lore")

PrimaryStatsTable.character = Relationship(back_populates="primary_stats")

SessionTable.chat = Relationship(back_populates="game_session")


async def get_game_registry():
    return SQLModel.metadata
