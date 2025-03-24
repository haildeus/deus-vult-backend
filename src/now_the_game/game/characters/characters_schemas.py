from enum import Enum

from sqlmodel import Field

from ...core.base import BaseSchema


class SupportedClasses(Enum):
    FARMER = "farmer"
    PRIEST = "priest"
    WARRIOR = "warrior"
    RULER = "ruler"


class LoreBase(BaseSchema):
    character_id: int = Field(foreign_key="characters.character_id")

    name: str = Field(..., description="Name of the character")
    appearance: str = Field(..., description="Appearance of the character")
    background: str = Field(..., description="Background of the character")
    class_name: SupportedClasses = Field(..., description="Class of the character")


class PrimaryStatsBase(BaseSchema):
    character_id: int = Field(foreign_key="characters.character_id")

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
    chat_id: int = Field(foreign_key="chats.object_id")
    user_id: int = Field(foreign_key="users.object_id")
