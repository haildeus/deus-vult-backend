from enum import Enum

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from src import BaseSchema, EventPayload
from src.api.craft.craft_interfaces import ICraftElementEvent

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "api.craft.recipes"

"""
ENUMS
"""


class RecipeTopics(Enum):
    # Create
    RECIPE_CREATE = f"{EVENT_BUS_PREFIX}.create"
    # Fetch
    RECIPE_FETCH = f"{EVENT_BUS_PREFIX}.fetch"
    RECIPE_FETCH_RESPONSE = f"{EVENT_BUS_PREFIX}.fetch.response"


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
PAYLOADS
"""


class CreateRecipePayload(CreateRecipe):
    db_session: AsyncSession


class FetchRecipePayload(FetchRecipe):
    db_session: AsyncSession


class FetchRecipeResponsePayload(EventPayload):
    recipes: list["RecipeBase"]


"""
EVENTS
"""


class CreateRecipeEvent(ICraftElementEvent):
    topic: str = RecipeTopics.RECIPE_CREATE.value
    payload: CreateRecipePayload  # type: ignore


class FetchRecipeEvent(ICraftElementEvent):
    topic: str = RecipeTopics.RECIPE_FETCH.value
    payload: FetchRecipePayload  # type: ignore


"""
TABLES
"""


class RecipeBase(BaseSchema):
    element_a_id: int = Field(foreign_key="elements.object_id", index=True)
    element_b_id: int = Field(foreign_key="elements.object_id", index=True)
    result_id: int = Field(foreign_key="elements.object_id", index=True)


class RecipeTable(RecipeBase, table=True):
    __tablename__ = "recipes"  # type: ignore

    __table_args__ = (
        # Ensure a+b is unique
        UniqueConstraint("element_a_id", "element_b_id", name="uq_recipe_element_pair"),
        # Enforce canonical order (a < b)
        CheckConstraint(
            "element_a_id < element_b_id", name="ck_recipe_canonical_order"
        ),
    )
