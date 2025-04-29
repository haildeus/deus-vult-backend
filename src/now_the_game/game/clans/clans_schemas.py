from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from src.shared.base import BaseSchema

if TYPE_CHECKING:
    from src.now_the_game.telegram.chats.chats_schemas import ChatTable


"""
TABLES
"""


class ClanBase(BaseSchema):
    name: str = Field(max_length=128, nullable=False, index=True)

    # --- Relationships ---
    chat_id: int = Field(foreign_key="chats.object_id", index=True)
    chat_instance: int | None = Field(foreign_key="chats.chat_instance", index=True)


class ClanTable(ClanBase, table=True):
    __tablename__ = "clans"  # type: ignore

    # --- Relationships ---
    chat: Optional["ChatTable"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[ClanTable.chat_id]",
        },
    )
