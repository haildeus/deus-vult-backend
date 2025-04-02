from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field

from src.api.craft.craft_interfaces import ICraftElementEvent
from src.shared.base import BaseSchema
from src.shared.event_registry import RecipeTopics
from src.shared.events import EventPayload

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
