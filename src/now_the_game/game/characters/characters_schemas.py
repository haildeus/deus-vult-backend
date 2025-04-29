from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from src.shared.base import BaseSchema

if TYPE_CHECKING:
    from src.now_the_game.game.clans.clans_schemas import ClanTable
    from src.now_the_game.telegram.users.users_schemas import UserTable


class CharacterBase(BaseSchema):
    name: str = Field(max_length=128, nullable=False, index=True)

    # --- Stats ---
    health: int = Field(default=100, ge=0, le=100)
    energy: int = Field(default=100, ge=0, le=100)

    # --- Relationships ---
    selected_clan_id: int = Field(foreign_key="clans.object_id", index=True)
    user_id: int = Field(foreign_key="users.object_id", index=True)


class CharacterTable(CharacterBase, table=True):
    __tablename__ = "characters"  # type: ignore

    # --- Relationships ---
    clan: Optional["ClanTable"] = Relationship(
        back_populates="characters",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[CharacterTable.clan_id]",
        },
    )
    user: Optional["UserTable"] = Relationship(
        back_populates="characters",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[CharacterTable.user_id]",
        },
    )
