import asyncio

from fastapi import HTTPException

from src.api import logger
from src.api.craft.elements.elements_schemas import ElementBase, ElementBaseInput
from src.api.craft.progress.progress_schemas import ProgressBase
from src.api.craft.recipes.recipes_schemas import RecipeBase
from src.shared.cache import disk_cache, generate_cache_key, get_disk_cache
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


@disk_cache(param_name="user_id", ttl=60 * 60 * 24)  # Cache for 1 day
async def fetch_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
) -> list[ProgressBase]:
    """Fetch progress"""
    async with uow.start():
        progress_event = Event.from_dict(
            ProgressTopics.PROGRESS_FETCH.value,
            {"user_id": user_id},
        )
        progress_response = await event_bus.request(progress_event)
        return progress_response.payload


async def create_progress(
    user_id: int,
    element_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
    chat_instance: int = 0,
) -> None:
    """Save user progress"""
    async with uow.start():
        create_progress_event = Event.from_dict(
            ProgressTopics.PROGRESS_CREATE.value,
            {
                "user_id": user_id,
                "element_id": element_id,
                "chat_instance": chat_instance,
            },
        )
        # TODO: Check if we need await here
        await event_bus.publish(create_progress_event)

        # Invalidate fetch_progress cache for this user
        cache = get_disk_cache()
        cache_key_to_invalidate = generate_cache_key(
            fetch_progress, "user_id", {"user_id": user_id}
        )
        deleted_count = cache.delete(cache_key_to_invalidate)  # type: ignore
        if deleted_count > 0:
            logger.info(f"Invalidated cache for key: {cache_key_to_invalidate}")
        else:
            logger.warning(
                f"Cache key not found for invalidation: {cache_key_to_invalidate}"
            )


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
    """Get element from Gemini & save to elements database"""
    async with uow.start():
        elements_input = ElementBaseInput(element_a=element_a, element_b=element_b)
        agent_event = Event.from_dict(
            ElementTopics.ELEMENT_COMBINATION.value, elements_input.model_dump()
        )
        agent_response = await event_bus.request(agent_event)
        element = agent_response.payload
        add_element_event = Event.from_dict(
            ElementTopics.ELEMENT_CREATE.value, element.model_dump()
        )
        # TODO: Check if we need await here
        await event_bus.publish(add_element_event)

        logger.debug(f"Element: {element}")
        return element
