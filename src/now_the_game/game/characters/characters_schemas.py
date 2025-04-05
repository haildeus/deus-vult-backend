from enum import Enum

from sqlmodel import Field

from src.shared.base import BaseSchema


class SupportedClasses(Enum):
    FARMER = "farmer"
    PRIEST = "priest"
    WARRIOR = "warrior"
    SCHOLAR = "scholar"


class LoreBase(BaseSchema):
    character_id: int = Field(foreign_key="characters.character_id", index=True)

    name: str = Field(..., description="Name of the character")
    appearance: str = Field(..., description="Appearance of the character")
    background: str = Field(..., description="Background of the character")
    class_name: SupportedClasses = Field(..., description="Class of the character")


class PrimaryStatsBase(BaseSchema):
    character_id: int = Field(foreign_key="characters.character_id", index=True)

    strength: int = Field(..., description="Strength of the character", ge=0, le=30)
    perception: int = Field(..., description="Perception of the character", ge=0, le=30)
    endurance: int = Field(..., description="Endurance of the character", ge=0, le=30)
    charisma: int = Field(..., description="Charisma of the character", ge=0, le=30)
    intelligence: int = Field(
        ..., description="Intelligence of the character", ge=0, le=30
    )
    agility: int = Field(..., description="Agility of the character", ge=0, le=30)
    luck: int = Field(..., description="Luck of the character", ge=0, le=30)


class CharacterBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.object_id", index=True)
    user_id: int = Field(foreign_key="users.object_id", index=True)


class CharacterTable(CharacterBase, table=True):
    __tablename__ = "characters"  # type: ignore


class LoreTable(LoreBase, table=True):
    __tablename__ = "lore"  # type: ignore


class PrimaryStatsTable(PrimaryStatsBase, table=True):
    __tablename__ = "primary_stats"  # type: ignore
