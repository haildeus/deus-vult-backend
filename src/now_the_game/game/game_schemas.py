from sqlmodel import Relationship

from .characters.characters_schemas import CharacterBase, LoreBase, PrimaryStatsBase
from .sessions.sessions_schemas import GameSessionBase


class CharacterTable(CharacterBase, table=True):
    __tablename__ = "characters"  # type: ignore

    lore: "LoreTable" = Relationship(back_populates="character")
    primary_stats: "PrimaryStatsTable" = Relationship(back_populates="character")


class LoreTable(LoreBase, table=True):
    __tablename__ = "lore"  # type: ignore

    character: CharacterTable = Relationship(back_populates="lore")


class PrimaryStatsTable(PrimaryStatsBase, table=True):
    __tablename__ = "primary_stats"  # type: ignore

    character: CharacterTable = Relationship(back_populates="primary_stats")


class GameSessionTable(GameSessionBase, table=True):
    __tablename__ = "game_sessions"  # type: ignore
