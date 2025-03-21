from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from ...core.base import BaseModel


class SupportedClasses(Enum):
    FARMER = "farmer"
    PRIEST = "priest"
    WARRIOR = "warrior"
    RULER = "ruler"


class LoreBase(SQLModel):
    character_id: UUID = Field(foreign_key="characters.character_id")

    name: str = Field(..., description="Name of the character")
    appearance: str = Field(..., description="Appearance of the character")
    background: str = Field(..., description="Background of the character")
    class_name: SupportedClasses = Field(..., description="Class of the character")


class PrimaryStatsBase(SQLModel):
    character_id: UUID = Field(foreign_key="characters.character_id")

    strength: int = Field(..., description="Strength of the character", ge=0, le=30)
    perception: int = Field(..., description="Perception of the character", ge=0, le=30)
    endurance: int = Field(..., description="Endurance of the character", ge=0, le=30)
    charisma: int = Field(..., description="Charisma of the character", ge=0, le=30)
    intelligence: int = Field(
        ..., description="Intelligence of the character", ge=0, le=30
    )
    agility: int = Field(..., description="Agility of the character", ge=0, le=30)
    luck: int = Field(..., description="Luck of the character", ge=0, le=30)


class CharacterBase(SQLModel):
    character_id: UUID = Field(
        ..., description="ID of the character", default_factory=uuid4()
    )


class Character(CharacterBase, table=True):
    __tablename__ = "characters"

    lore: LoreBase = Relationship(back_populates="character")
    primary_stats: PrimaryStatsBase = Relationship(back_populates="character")


class Lore(LoreBase, table=True):
    __tablename__ = "lore"

    character: Character = Relationship(back_populates="lore")


class PrimaryStats(PrimaryStatsBase, table=True):
    __tablename__ = "primary_stats"

    character: Character = Relationship(back_populates="primary_stats")
