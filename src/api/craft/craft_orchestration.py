from fastapi import HTTPException

from src.api import logger
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementBase,
    ElementBaseInput,
    ElementTable,
)
from src.api.craft.progress.progress_schemas import ProgressTable
from src.api.craft.recipes.recipes_schemas import RecipeTable
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics, ProgressTopics, RecipeTopics
from src.shared.events import Event
from src.shared.uow import UnitOfWork

"""
PROGRESS
"""


async def fetch_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
) -> list[ProgressTable]:
    """Fetch progress"""
    logger.debug(f"Fetching progress for user {user_id} using event bus pattern.")
    async with uow.start():
        progress_event = Event.from_dict(
            ProgressTopics.PROGRESS_FETCH,
            {"user_id": user_id},
        )
        progress_response: list[ProgressTable] = await event_bus.request(progress_event)
        return progress_response

async def init_elements(
    uow: UnitOfWork,
    event_bus: EventBus,
) -> None:
    """Initialize elements for the user"""
    logger.debug(f"Initializing starting elements")
    async with uow.start():
        try:
            elements_init_event = Event.from_dict(
                ElementTopics.ELEMENTS_INIT,
            )
            await event_bus.request(elements_init_event)
            logger.debug(f"Initialized starting elements.")
        except Exception as e:
            logger.error(f"Error initializing starting elements: {e}")
            raise e

async def init_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
    chat_instance: int = 0,
) -> None:
    """Initialize progress for the user"""
    logger.debug(f"Initializing progress for user {user_id}.")
    async with uow.start():
        try:
            elements_fetch_event = Event.from_dict(
                ElementTopics.ELEMENTS_FETCH_INIT,
            )
            elements_fetch_response: list[ElementTable] = await event_bus.request(elements_fetch_event)
            element_ids = [element.object_id for element in elements_fetch_response]
            logger.debug(f"Fetched {len(element_ids)} elements for user {user_id}.")
        except Exception as e:
            logger.error(f"Error initializing elements: {e}")
            raise e
        try:
            init_progress_event = Event.from_dict(
                ProgressTopics.PROGRESS_INIT,
                {"user_id": user_id, "chat_instance": chat_instance, "starting_elements_ids": element_ids},
            )
            await event_bus.request(init_progress_event)
            logger.debug(f"Initialized progress for user {user_id}.")
        except Exception as e:
            logger.error(f"Error initializing progress: {e}")
            raise e


async def get_element_from_gemini(
    uow: UnitOfWork, event_bus: EventBus, element_a: ElementBase, element_b: ElementBase
) -> ElementBase:
    """Get element from Gemini & save to elements database"""
    async with uow.start():
        elements_input = ElementBaseInput(element_a=element_a, element_b=element_b)
        # Fetch element from Gemini
        agent_event = Event.from_dict(
            ElementTopics.ELEMENT_COMBINATION.value, elements_input.model_dump()
        )
        agent_response = await event_bus.request(agent_event)
        element = agent_response.payload
        # Add element to database
        add_element_event = Event.from_dict(
            ElementTopics.ELEMENT_CREATE.value, element.model_dump()
        )
        # TODO: Check if we need await here
        await event_bus.publish(add_element_event)
        # TODO: Add element to the recipe database

        logger.debug(f"Element: {element}")
        return element


# --- Main Orchestration Logic ---


async def orchestrate_element_combination(
    user_id: int,
    element_a_id: int,
    element_b_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
    chat_instance: int = 0,
) -> None:
    """
    Orchestrates the element combination process within a single transaction.
    """
    result_element_table: ElementTable | None = None

    async with uow.start():
        # Check access
        check_progress_event = Event.from_dict(
            ProgressTopics.PROGRESS_CHECK,
            {
                "user_id": user_id,
                "element_a_id": element_a_id,
                "element_b_id": element_b_id,
            },
        )
        await event_bus.request(check_progress_event)

        # Check for existing recipe (includes result element)
        find_recipe_event = Event.from_dict(
            RecipeTopics.RECIPE_FETCH,
            {
                "element_a_id": element_a_id,
                "element_b_id": element_b_id,
            },
        )
        recipe: list[RecipeTable] = await event_bus.request(find_recipe_event)

        if recipe and recipe[0].result:
            logger.debug(
                f"Found existing recipe: {recipe[0].object_id} -> "
                f"Result: {recipe[0].result.name} ({recipe[0].result.object_id})"
            )
            result_element_table = recipe[0].result
        else:
            logger.debug(
                f"No recipe found for {element_a_id} + {element_b_id}. Querying Gemini."
            )
            # Query Gemini, create Element and Recipe
            # Fetch Element A and B details needed for Gemini prompt
            element_a_event = Event.from_dict(
                ElementTopics.ELEMENT_FETCH,
                {"element_id": element_a_id},
            )
            element_b_event = Event.from_dict(
                ElementTopics.ELEMENT_FETCH,
                {"element_id": element_b_id},
            )
            element_a_table: list[ElementTable] = await event_bus.request(
                element_a_event
            )
            element_b_table: list[ElementTable] = await event_bus.request(
                element_b_event
            )

            if not element_a_table or not element_b_table:
                logger.error(
                    f"Could not fetch element details for Gemini call. "
                    f"A:{element_a_id}, B:{element_b_id}"
                )
                raise HTTPException(
                    status_code=500, detail="Internal error fetching element details"
                )

            try:
                # Call the Gemini function
                element_a_base = ElementBaseInput(
                    element_a=element_a_table[0], element_b=element_b_table[0]
                )
                element_b_base = ElementBaseInput(
                    element_a=element_b_table[0], element_b=element_a_table[0]
                )
                new_element_event = Event.from_dict(
                    ElementTopics.ELEMENT_COMBINATION,
                    {"element_a": element_a_base, "element_b": element_b_base},
                )
                new_element_generated: Element = await event_bus.request(
                    new_element_event
                )

                # Add element to database
                add_element_event = Event.from_dict(
                    ElementTopics.ELEMENT_CREATE, new_element_generated.model_dump()
                )
                new_created_element: list[ElementTable] = await event_bus.request(
                    add_element_event
                )

                result_element_table = new_created_element[0]
                logger.info(
                    f"Gemini process resulted in element: {result_element_table.name} "
                    f"({result_element_table.object_id})"
                )
                add_recipe_event = Event.from_dict(
                    RecipeTopics.RECIPE_CREATE,
                    {
                        "element_a_id": element_a_id,
                        "element_b_id": element_b_id,
                        "result_id": result_element_table.object_id,
                    },
                )
                await event_bus.request(add_recipe_event)

                # Create progress
                create_progress_event = Event.from_dict(
                    ProgressTopics.PROGRESS_CREATE,
                    {
                        "user_id": user_id,
                        "chat_instance": chat_instance,
                        "element_id": result_element_table.object_id,
                    },
                )
                await event_bus.request(create_progress_event)

            except Exception as e:
                logger.error(
                    f"Error during Gemini interaction or atomic recipe creation: {e}",
                    exc_info=True,
                )
                # Check if it's an HTTPException and re-raise, otherwise wrap
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(
                    status_code=500, detail=f"Failed to get combination result: {e}"
                ) from e
