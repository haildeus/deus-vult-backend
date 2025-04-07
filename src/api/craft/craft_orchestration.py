import asyncio

from fastapi import HTTPException

from src.api import logger
from src.api.craft.elements.elements_schemas import ElementBase, ElementBaseInput
from src.api.craft.progress.progress_schemas import ProgressBase
from src.api.craft.recipes.recipes_schemas import RecipeBase
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics, ProgressTopics, RecipeTopics
from src.shared.events import Event
from src.shared.uow import UnitOfWork

"""
PROGRESS
"""


async def check_access_to_elements(
    uow: UnitOfWork,
    event_bus: EventBus,
    user_id: int,
    element_a: ElementBase,
    element_b: ElementBase,
) -> bool:
    """Checks if users have these elements unlocked"""
    async with uow.start():
        progress_event_a = Event.from_dict(
            ProgressTopics.PROGRESS_EXISTS.value,
            {
                "user_id": user_id,
                "element_a": element_a,
            },
        )
        progress_event_b = Event.from_dict(
            ProgressTopics.PROGRESS_EXISTS.value,
            {
                "user_id": user_id,
                "element_b": element_b,
            },
        )
        event_a, event_b = await asyncio.gather(
            event_bus.request(progress_event_a),
            event_bus.request(progress_event_b),
        )
        if event_a.payload.exists and event_b.payload.exists:
            logger.debug(
                f"User {user_id} has access to element {element_a} and {element_b}"
            )
            return True
        else:
            logger.error(
                f"User {user_id} does not have access to element {element_a} or {element_b}"  # noqa: E501
            )
            raise HTTPException(
                status_code=400, detail="You don't have access to this element"
            )


async def fetch_progress(
    uow: UnitOfWork,
    event_bus: EventBus,
    user_id: int,
) -> list[ProgressBase]:
    """Fetch progress"""
    async with uow.start():
        progress_event = Event.from_dict(
            ProgressTopics.PROGRESS_FETCH.value,
            {"user_id": user_id},
        )
        progress_response = await event_bus.request(progress_event)
        return progress_response.payload


"""
RECIPE
"""


async def check_recipe(
    uow: UnitOfWork, event_bus: EventBus, element_a: ElementBase, element_b: ElementBase
) -> RecipeBase | None:
    """Check if there is a recipe for the given elements"""
    async with uow.start():
        recipe_event = Event.from_dict(
            RecipeTopics.RECIPE_FETCH.value,
            {
                "element_a": element_a,
                "element_b": element_b,
            },
        )
        recipe_response = await event_bus.request(recipe_event)
        if recipe_response.payload.recipes and len(recipe_response.payload.recipes) > 0:
            logger.debug(f"Recipes: {recipe_response.payload.recipes}")
            recipe = recipe_response.payload.recipes[0]
            return recipe
        else:
            logger.error(f"No recipes found for elements {element_a} and {element_b}")
            return None


"""
ELEMENT
"""


async def get_element_from_db(
    uow: UnitOfWork, event_bus: EventBus, element_id: int
) -> ElementBase:
    """Get element from database"""
    async with uow.start():
        element_event = Event.from_dict(
            ElementTopics.ELEMENT_FETCH.value,
            {
                "element_id": element_id,
            },
        )
        element_response = await event_bus.request(element_event)
        element = element_response.payload.elements[0]

        logger.debug(f"Element: {element}")
        return element


"""
AGENT
"""


async def get_element_from_gemini(
    uow: UnitOfWork, event_bus: EventBus, element_a: ElementBase, element_b: ElementBase
) -> ElementBase:
    """Get element from Gemini"""
    async with uow.start():
        elements_input = ElementBaseInput(element_a=element_a, element_b=element_b)
        event = Event.from_dict(
            ElementTopics.ELEMENT_COMBINATION.value, elements_input.model_dump()
        )
        response = await event_bus.request(event)
        logger.debug(f"Element: {response.payload}")
        return response.payload
