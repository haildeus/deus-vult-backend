import logging
import random

from fastapi import HTTPException

from src.api.craft.craft_constants import CHANCE_FOR_REPEAT_ELEMENT
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
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork

logger = logging.getLogger("deus-vult.api.craft")


@async_traced_function
async def fetch_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
) -> list[ProgressResponse]:
    """Fetch progress"""
    logger.debug("Fetching progress for user %s using event bus pattern.", user_id)
    async with uow.start():
        try:
            progress_response: list[ProgressTable] = await event_bus.request(
                ProgressTopics.PROGRESS_FETCH,
                user_id=user_id,
            )
        except Exception as e:
            logger.error("Error fetching progress: %s", e)
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
            logger.exception("Error fetching progress: %s", e)
            raise e


@async_traced_function
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
            logger.error("Error initializing starting elements: %s", e)
            raise e


@async_traced_function
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
            logger.error("Error fetching initial elements: %s", e)
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
            logger.error("Error fetching initial elements: %s", e)
            raise e


@async_traced_function
async def __repeat_element_proc(
    element_a: ElementTable,
    element_b: ElementTable,
    chance_for_repeat_element: float = CHANCE_FOR_REPEAT_ELEMENT,
) -> ElementTable | None:
    """
    Roll for a repeat element

    If the roll is successful, return the repeat element.
    If the roll is not successful, return None.
    """
    uniform_distribution = random.uniform(0, 1)
    # if elements are the same, double the chance
    if element_a.object_id == element_b.object_id:
        chance_for_repeat_element *= 2

    if uniform_distribution < chance_for_repeat_element:
        return random.choice([element_a, element_b])
    else:
        return None


@async_traced_function
async def init_progress(
    user_id: int,
    uow: UnitOfWork,
    event_bus: EventBus,
    chat_instance: int = 0,
) -> None:
    """Initialize progress for the user"""
    logger.debug("Initializing progress for user %s.", user_id)
    async with uow.start():
        try:
            elements_fetch_response: list[ElementTable] = await event_bus.request(
                ElementTopics.ELEMENTS_FETCH_INIT
            )
            element_ids = [element.object_id for element in elements_fetch_response]
            logger.debug("Fetched %s elements for user %s.", len(element_ids), user_id)
        except Exception as e:
            logger.error("Error initializing elements: %s", e)
            raise e
        try:
            await event_bus.request(
                ProgressTopics.PROGRESS_INIT,
                user_id=user_id,
                chat_instance=chat_instance,
                starting_elements_ids=element_ids,
            )
            logger.debug("Initialized progress for user %s.", user_id)
        except Exception as e:
            logger.error("Error initializing progress: %s", e)
            raise e


@async_traced_function
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
            logger.error("Error checking progress: %s", e)
            raise e

        # Check for existing recipe
        try:
            recipe: list[RecipeTable] = await event_bus.request(
                RecipeTopics.RECIPE_FETCH,
                element_a_id=element_a_id,
                element_b_id=element_b_id,
            )
        except Exception as e:
            logger.error("Error fetching recipe: %s", e)
            raise e

        if recipe and recipe[0].result:
            result_element_table = recipe[0].result
            logger.debug("Found existing recipe: %s ->", result_element_table.object_id)
            logger.debug(
                "Result: %s (%s)",
                result_element_table.name,
                result_element_table.object_id,
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
                "No recipe found for %s + %s. Querying Gemini.",
                element_a_id,
                element_b_id,
            )
            # Query Gemini, create Element and Recipe
            fetched_elements: list[ElementTable] = await event_bus.request(
                ElementTopics.ELEMENT_FETCH,
                element_id=[element_a_id, element_b_id],
            )
            element_a = fetched_elements[0]
            element_b = fetched_elements[1]

            # Return repeat element based on chance
            repeat_element_proc = await __repeat_element_proc(element_a, element_b)
            if repeat_element_proc:
                result_element_table = repeat_element_proc
            # If no repeat element, call Gemini generation
            else:
                try:
                    input_a = Element.model_validate(fetched_elements[0].model_dump())
                    input_b = Element.model_validate(fetched_elements[1].model_dump())
                    agent_input = ElementInput(element_a=input_a, element_b=input_b)

                    # Call the Gemini function
                    new_element_generated: Element = await event_bus.request(
                        ElementTopics.ELEMENT_COMBINATION,
                        **agent_input.model_dump(),
                    )

                    add_element_response: list[ElementTable] = await event_bus.request(
                        ElementTopics.ELEMENT_CREATE,
                        **new_element_generated.model_dump(),
                    )
                    result_element_table = add_element_response[0]

                except Exception as e:
                    logger.error(
                        "Error during Gemini interaction "
                        + "or atomic recipe creation: {e}",
                        exc_info=True,
                    )
                    if isinstance(e, HTTPException):
                        raise e
                    raise HTTPException(
                        status_code=500, detail=f"Failed to get combination result: {e}"
                    ) from e

            session = await uow.get_session()
            await session.commit()

            # Do it in the second transaction to comply with foreign key constraints
            try:
                await event_bus.request(
                    RecipeTopics.RECIPE_CREATE,
                    element_a_id=element_a_id,
                    element_b_id=element_b_id,
                    result_id=result_element_table.object_id,
                )

                await event_bus.request(
                    ProgressTopics.PROGRESS_CREATE,
                    user_id=user_id,
                    chat_instance=chat_instance,
                    element_id=result_element_table.object_id,
                )
            except Exception as e:
                logger.error("Error creating progress: %s", e)
                raise HTTPException(
                    status_code=500, detail=f"Failed to create progress: {e}"
                ) from e

        return ElementResponse(
            object_id=result_element_table.object_id,
            name=result_element_table.name,
            emoji=result_element_table.emoji,
        )
