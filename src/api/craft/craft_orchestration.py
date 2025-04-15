from fastapi import HTTPException

from src.api import logger
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementInput,
    ElementResponse,
    ElementTable,
)
from src.api.craft.progress.progress_schemas import ProgressResponse, ProgressTable
from src.api.craft.recipes.recipes_schemas import RecipeTable
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics, ProgressTopics, RecipeTopics
from src.shared.uow import UnitOfWork

"""
PROGRESS
"""


async def fetch_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
) -> list[ProgressResponse]:
    """Fetch progress"""
    logger.debug(f"Fetching progress for user {user_id} using event bus pattern.")
    async with uow.start():
        try:
            progress_response: list[ProgressTable] = await event_bus.request(
                ProgressTopics.PROGRESS_FETCH,
                user_id=user_id,
            )
        except Exception as e:
            logger.error(f"Error fetching progress: {e}")
            raise e

        try:
            return [
                ProgressResponse(
                    user_id=progress.object_id,
                    chat_instance=progress.chat_instance,
                    object_id=progress.element_id,
                    name=progress.element.name,  # type: ignore
                    emoji=progress.element.emoji,  # type: ignore
                )
                for progress in progress_response
            ]
        except Exception as e:
            logger.error(f"Error fetching progress: {e}")
            raise e


async def init_elements(
    uow: UnitOfWork,
    event_bus: EventBus,
) -> None:
    """Initialize elements for the user"""
    logger.debug("Initializing starting elements")
    async with uow.start():
        try:
            await event_bus.request(ElementTopics.ELEMENTS_INIT)
            logger.debug("Initialized starting elements.")
        except Exception as e:
            logger.error(f"Error initializing starting elements: {e}")
            raise e


async def fetch_init_elements(
    uow: UnitOfWork,
    event_bus: EventBus,
) -> list[ElementResponse]:
    """Fetch initial elements"""
    async with uow.start():
        try:
            elements_fetch_response: list[ElementTable] = await event_bus.request(
                ElementTopics.ELEMENTS_FETCH_INIT
            )
        except Exception as e:
            logger.error(f"Error fetching initial elements: {e}")
            raise e

        try:
            return [
                ElementResponse(
                    object_id=element.object_id,
                    name=element.name,
                    emoji=element.emoji,
                )
                for element in elements_fetch_response
            ]
        except Exception as e:
            logger.error(f"Error fetching initial elements: {e}")
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
            elements_fetch_response: list[ElementTable] = await event_bus.request(
                ElementTopics.ELEMENTS_FETCH_INIT
            )
            element_ids = [element.object_id for element in elements_fetch_response]
            logger.debug(f"Fetched {len(element_ids)} elements for user {user_id}.")
        except Exception as e:
            logger.error(f"Error initializing elements: {e}")
            raise e
        try:
            await event_bus.request(
                ProgressTopics.PROGRESS_INIT,
                user_id=user_id,
                chat_instance=chat_instance,
                starting_elements_ids=element_ids,
            )
            logger.debug(f"Initialized progress for user {user_id}.")
        except Exception as e:
            logger.error(f"Error initializing progress: {e}")
            raise e


async def orchestrate_element_combination(
    user_id: int,
    element_a_id: int,
    element_b_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
    chat_instance: int = 0,
) -> ElementResponse:
    """
    Orchestrates the element combination process within a single transaction.
    """
    async with uow.start():
        # Check access
        try:
            await event_bus.request(
                ProgressTopics.PROGRESS_CHECK,
                user_id=user_id,
                element_a_id=element_a_id,
                element_b_id=element_b_id,
            )
        except Exception as e:
            logger.error(f"Error checking progress: {e}")
            raise e

        # Check for existing recipe
        try:
            recipe: list[RecipeTable] = await event_bus.request(
                RecipeTopics.RECIPE_FETCH,
                element_a_id=element_a_id,
                element_b_id=element_b_id,
            )
        except Exception as e:
            logger.error(f"Error fetching recipe: {e}")
            raise e

        if recipe and recipe[0].result:
            result_element_table = recipe[0].result
            logger.debug(
                f"Found existing recipe: {result_element_table.object_id} -> "
                + f"Result: {result_element_table.name} "
                + f"({result_element_table.object_id})",
            )

            # Adds progress if it doesn't exist, checks in progress model
            await event_bus.request(
                ProgressTopics.PROGRESS_CREATE,
                user_id=user_id,
                chat_instance=chat_instance,
                element_id=result_element_table.object_id,
            )

            return ElementResponse(
                object_id=result_element_table.object_id,
                name=result_element_table.name,
                emoji=result_element_table.emoji,
            )
        else:
            logger.debug(
                f"No recipe found for {element_a_id} + {element_b_id}. Querying Gemini."
            )
            # Query Gemini, create Element and Recipe
            fetched_elements: list[ElementTable] = await event_bus.request(
                ElementTopics.ELEMENT_FETCH,
                element_id=[element_a_id, element_b_id],
            )
            input_a = Element.model_validate(fetched_elements[0].model_dump())
            input_b = Element.model_validate(fetched_elements[1].model_dump())
            agent_input = ElementInput(element_a=input_a, element_b=input_b)

            try:
                # Call the Gemini function
                new_element_generated: Element = await event_bus.request(
                    ElementTopics.ELEMENT_COMBINATION,
                    **agent_input.model_dump(),
                )

                # Add element to database if it doesn't exist
                # Returns the element if it exists
                add_element_response: list[ElementTable] = await event_bus.request(
                    ElementTopics.ELEMENT_CREATE,
                    **new_element_generated.model_dump(),
                )
                result_element_table: ElementTable = add_element_response[0]

                # Add recipe to database
                await event_bus.request(
                    RecipeTopics.RECIPE_CREATE,
                    element_a_id=element_a_id,
                    element_b_id=element_b_id,
                    result_id=result_element_table.object_id,
                )

                # Create progress
                await event_bus.request(
                    ProgressTopics.PROGRESS_CREATE,
                    user_id=user_id,
                    chat_instance=chat_instance,
                    element_id=result_element_table.object_id,
                )

                return ElementResponse(
                    object_id=result_element_table.object_id,
                    name=result_element_table.name,
                    emoji=result_element_table.emoji,
                )

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
