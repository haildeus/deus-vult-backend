from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, model_validator
from sqlmodel import Field, Relationship

from src.shared.base import BaseSchema
from src.shared.events import EventPayload

if TYPE_CHECKING:
    from src.api.craft.elements.elements_schemas import ElementTable


"""
MODELS
"""


class Progress(EventPayload):
    user_id: int
    chat_instance: int
    element_id: int


class CheckProgress(EventPayload):
    user_id: int
    element_a_id: int
    element_b_id: int


class FetchProgress(EventPayload):
    user_id: int | None = None
    chat_instance: int | None = None
    element_id: int | None = None

    @model_validator(mode="before")
    def validate_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Checking that at least one of the two parameters is provided"""
        if not values.get("user_id") and not values.get("chat_instance"):
            raise ValueError("Either user_id or chat_instance must be provided")
        return values


class InitProgress(EventPayload):
    user_id: int
    chat_instance: int
    starting_elements_ids: list[int]


class ProgressResponse(BaseModel):
    """
    Response model for progress.
    """

    # --- User ---
    user_id: int
    chat_instance: int

    # --- Element ---
    object_id: int
    name: str
    emoji: str


class ProgressBase(BaseSchema):
    chat_instance: int = Field(primary_key=True, index=True)
    element_id: int = Field(
        primary_key=True,
        foreign_key="elements.object_id",
        index=True,
    )


class ProgressTable(ProgressBase, table=True):
    __tablename__ = "progress"  # type: ignore

    # --- Add Relationship Type Hints ---
    element: Optional["ElementTable"] = Relationship(
        back_populates="progress",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[ProgressTable.element_id]",
        },
    )
