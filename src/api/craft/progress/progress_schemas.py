from typing import Any

from pydantic import model_validator
from sqlmodel import Field

from src.shared.base import BaseSchema
from src.shared.events import EventPayload

"""
MODELS
"""


class Progress(EventPayload):
    user_id: int
    chat_instance: int
    element_id: int


"""
PAYLOADS
"""


class CreateProgress(Progress):
    pass


class FetchProgress(EventPayload):
    user_id: int | None = None
    chat_instance: int | None = None

    @model_validator(mode="before")
    def validate_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Checking that at least one of the two parameters is provided"""
        if not values.get("user_id") and not values.get("chat_instance"):
            raise ValueError("Either user_id or chat_instance must be provided")
        return values


"""
EVENTS
"""

"""
TABLES
"""


# TODO: chat_instance should be connected to sessions
# TODO: primary keys should be object_id and chat_instance
class ProgressBase(BaseSchema):
    chat_instance: int = Field(index=True)
    element_id: int = Field(foreign_key="elements.object_id", index=True)


class ProgressTable(ProgressBase, table=True):
    __tablename__ = "progress"  # type: ignore
