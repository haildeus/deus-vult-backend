import re
from typing import TYPE_CHECKING, Annotated, Any

import emoji
from pydantic import BaseModel, field_validator, model_validator
from sqlmodel import Field, Relationship

from src.shared.base import BaseSchema
from src.shared.events import EventPayload

# Forward reference for type hints
if TYPE_CHECKING:
    from src.api.craft.progress.progress_schemas import ProgressTable
    from src.api.craft.recipes.recipes_schemas import RecipeTable


class Element(EventPayload):
    """
    Base model for an element class.

    Attributes:
        - name: The name of the element
        - emoji: The emoji representing the element.
    """

    name: Annotated[str, Field(max_length=100, description="The name of the element")]
    emoji: Annotated[
        str, Field(max_length=10, description="The emoji representing the element")
    ]

    # noinspection PyNestedDecorators
    @field_validator("emoji")
    @classmethod
    def validate_is_proper_emoji(cls, v: str) -> str:
        """Validate that the input string is a single, valid emoji."""
        if not v:
            raise ValueError("Emoji field cannot be empty")

        if not emoji.is_emoji(v):
            raise ValueError(f"'{v}' is not recognized as a valid emoji.")

        if re.search(r"\s", v):
            raise ValueError("Emoji must not contain spaces")

        return v


"""
API MODELS
"""


class ElementResponse(BaseModel):
    object_id: int = Field(ge=1, description="The unique identifier for the element")
    name: str = Field(max_length=100, description="The name of the element")
    emoji: str = Field(max_length=10, description="The emoji representing the element")


class ElementApiInput(BaseModel):
    object_id_a: int = Field(ge=1, description="The unique identifier for the element")
    object_id_b: int = Field(ge=1, description="The unique identifier for the element")


"""
EVENT MODELS
"""


class CreateElement(Element):
    pass


class FetchElement(EventPayload):
    element_id: int | list[int] | None = None
    name: str | list[str] | None = None

    @model_validator(mode="before")
    def validate_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("element_id") and values.get("name"):
            raise ValueError("Only one of element_id or name must be provided")
        return values


"""
PAYLOADS
"""


class CreateElementPayload(CreateElement):
    pass


class FetchElementResponsePayload(EventPayload):
    elements: list["ElementTable"]


"""
TABLES
"""


class ElementBase(BaseSchema):
    name: str = Field(index=True, unique=True, max_length=100)
    emoji: str = Field(max_length=10)


class ElementTable(ElementBase, table=True):
    __tablename__ = "elements"  # type: ignore

    # --- Add Back-Populating Relationship Type Hints ---
    recipes_as_a: list["RecipeTable"] = Relationship(
        back_populates="element_a",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_a_id]",
            "cascade": "all, delete-orphan",
        },
    )
    recipes_as_b: list["RecipeTable"] = Relationship(
        back_populates="element_b",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_b_id]",
            "cascade": "all, delete-orphan",
        },
    )
    recipes_as_result: list["RecipeTable"] = Relationship(
        back_populates="result",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.result_id]",
            "cascade": "all, delete-orphan",
        },
    )
    progress: list["ProgressTable"] = Relationship(
        back_populates="element",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[ProgressTable.element_id]",
            "cascade": "all, delete-orphan",
        },
    )
    # --- End Back-Populating Relationship Type Hints ---


"""
AGENTIC MODELS
"""


class ElementBaseInput(EventPayload):
    element_a: ElementBase
    element_b: ElementBase


class ElementInput(EventPayload):
    element_a: Element
    element_b: Element

    @classmethod
    def from_base(cls, element_input: ElementBaseInput) -> "ElementInput":
        element_a = Element(
            name=element_input.element_a.name, emoji=element_input.element_a.emoji
        )
        element_b = Element(
            name=element_input.element_b.name, emoji=element_input.element_b.emoji
        )
        return cls(element_a=element_a, element_b=element_b)


class ElementOutput(EventPayload):
    reason: str = Field(max_length=150, description="The reason for the combination")
    result: Element = Field(description="The result of the combination")
