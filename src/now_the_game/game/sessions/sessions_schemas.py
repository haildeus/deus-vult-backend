from datetime import datetime

from sqlmodel import Field

from src.shared.base import BaseSchema


class GameSessionBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.object_id", index=True)
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())


class GameSessionTable(GameSessionBase, table=True):
    __tablename__ = "game_sessions"  # type: ignore
