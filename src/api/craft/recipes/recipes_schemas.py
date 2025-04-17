from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship

from src.shared.base import BaseSchema
from src.shared.events import EventPayload

# Forward reference for type hints
if TYPE_CHECKING:
    from src.api.craft.elements.elements_schemas import ElementTable

"""
MODELS
"""


class CreateRecipe(EventPayload):
    element_a_id: int
    element_b_id: int
    result_id: int


class FetchRecipe(EventPayload):
    element_a_id: int | None = None
    element_b_id: int | None = None
    result_id: int | None = None


"""
TABLES
"""


class RecipeBase(BaseSchema):
    element_a_id: int = Field(foreign_key="elements.object_id", index=True)
    element_b_id: int = Field(foreign_key="elements.object_id", index=True)
    result_id: int = Field(foreign_key="elements.object_id", index=True)


class RecipeTable(RecipeBase, table=True):
    __tablename__ = "recipes"  # type: ignore

    # --- Add Relationship Type Hints ---
    element_a: Optional["ElementTable"] = Relationship(
        back_populates="recipes_as_a",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_a_id]",
        },
    )
    element_b: Optional["ElementTable"] = Relationship(
        back_populates="recipes_as_b",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_b_id]",
        },
    )
    result: Optional["ElementTable"] = Relationship(
        back_populates="recipes_as_result",
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.result_id]",
        },
    )
    # --- End Relationship Type Hints ---

    __table_args__ = (
        # Ensure a+b is unique
        UniqueConstraint("element_a_id", "element_b_id", name="uq_recipe_element_pair"),
        # Enforce canonical order (a < b)
        CheckConstraint(
            "element_a_id < element_b_id", name="ck_recipe_canonical_order"
        ),
    )
