from collections import Counter
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship

from src.shared.base import BaseSchema

# Forward reference for type hints
if TYPE_CHECKING:
    from src.api.craft.elements.elements_schemas import Element, ElementTable


class RecipeBase(BaseSchema):
    element_a_id: int = Field(foreign_key="elements.object_id", index=True)
    element_b_id: int = Field(foreign_key="elements.object_id", index=True)
    result_id: int = Field(foreign_key="elements.object_id", index=True)

    # element_id -> count
    resources_cost: dict[str, int] = Field(sa_column=Column(JSONB))

    discovered_count: int = Field(default=0)


class RecipePublic(RecipeBase):
    pass


class RecipeWithElementsPublic(RecipeBase):
    element_a: Optional["Element"]
    element_b: Optional["Element"]
    result: Optional["Element"]


class RecipesListResponse(BaseModel):
    recipes: list[RecipeWithElementsPublic]


class RecipeTable(RecipeBase, table=True):
    __tablename__ = "recipes"  # type: ignore

    # --- Add Relationship Type Hints ---
    element_a: Optional["ElementTable"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_a_id]",
        },
    )
    element_b: Optional["ElementTable"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[RecipeTable.element_b_id]",
        },
    )
    result: "ElementTable" = Relationship(
        back_populates="recipe",
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

    def update_resources_cost(
        self, element_a: "ElementTable", element_b: "ElementTable"
    ) -> None:
        left_costs = {}
        if element_a.recipe is None:
            # Base resource
            left_costs[str(element_a.object_id)] = 1
        else:
            left_costs.update(element_a.recipe.resources_cost)

        right_costs = {}
        if element_b.recipe is None:
            right_costs[str(element_b.object_id)] = 1
        else:
            right_costs.update(element_b.recipe.resources_cost)

        total_cost = Counter(left_costs)
        total_cost.update(right_costs)
        self.resources_cost = dict(total_cost)
