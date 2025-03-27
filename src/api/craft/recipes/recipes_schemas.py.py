from enum import Enum

from .... import BaseSchema, EventPayload
from ..craft_interfaces import ICraftRecipeEvent

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "api.craft.recipes"

"""
ENUMS
"""


class RecipeTopics(Enum):
    RECIPE_CREATED = f"{EVENT_BUS_PREFIX}.fetch"


"""
MODELS
"""


class RecipeCreatedPayload(EventPayload):
    pass


"""
EVENTS
"""


class RecipeCreatedEvent(ICraftRecipeEvent):
    topic: str = RecipeTopics.RECIPE_CREATED.value
    payload: RecipeCreatedPayload  # type: ignore


"""
TABLES
"""


class RecipeBase(BaseSchema):
    pass


class RecipeTable(RecipeBase, table=True):
    __tablename__ = "recipes"  # type: ignore
