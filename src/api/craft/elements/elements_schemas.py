import re
from typing import Annotated, Optional

import emoji
from pydantic import BaseModel, field_validator
from sqlmodel import Field, Relationship

from src.api.craft.recipes.recipes_schemas import RecipeBase, RecipeTable
from src.shared.base import BaseSchema
from src.shared.events import EventPayload


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
    recipe: RecipeBase = Field(description="The recipe that this element belongs to")

    is_first_discovered: bool = Field(
        description="Whether the element was discovered by this user before"
    )
    is_new: bool = Field(description="Whether the element was discovered before")


class CraftRequest(BaseModel):
    object_id_a: int = Field(ge=1, description="The unique identifier for the element")
    object_id_b: int = Field(ge=1, description="The unique identifier for the element")


"""
TABLES
"""


class ElementBase(BaseSchema):
    name: str = Field(index=True, unique=True, max_length=100)
    emoji: str = Field(max_length=10)


class ElementTable(ElementBase, table=True):
    __tablename__ = "elements"  # type: ignore

    recipe: Optional["RecipeTable"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.result_id]",
        }
    )


"""
AGENTIC MODELS
"""


class ElementInput(EventPayload):
    element_a: Element
    element_b: Element


class ElementOutput(EventPayload):
    reason: str = Field(max_length=150, description="The reason for the combination")
    result: Element = Field(description="The result of the combination")
