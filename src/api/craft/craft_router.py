from collections.abc import Callable
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src import Container
from src.api import logger
from src.api.core.dependencies import validate_init_data
from src.api.craft.craft_orchestration import (
    check_access_to_elements,
    check_recipe,
    create_progress,
    fetch_progress,
    get_element_from_db,
    get_element_from_gemini,
)
from src.api.craft.elements.elements_schemas import ElementBase
from src.api.craft.progress.progress_schemas import ProgressBase
from src.shared.event_bus import EventBus
from src.shared.uow import UnitOfWork

craft_router = APIRouter(prefix="/craft")


@craft_router.post(
    "/elements/combine",
    name="Combining elements",
    response_model=ElementBase,
    status_code=201,
    tags=["Elements"],
)
@inject
async def combine_elements(
    user_id: Annotated[int, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow_factory: Annotated[
        Callable[[], UnitOfWork], Depends(Provide[Container.uow_factory])
    ],
    element_a: ElementBase,
    element_b: ElementBase,
) -> ElementBase:
    """Combine elements"""
    logger.debug(f"Combining elements: {element_a} and {element_b}")
    try:
        assert element_a
        assert element_b
    except AssertionError as e:
        raise HTTPException(status_code=400, detail="Invalid elements") from e

    uow = uow_factory()
    # Step 1: Check if these elements exist in progress for the user
    try:
        await check_access_to_elements(uow, event_bus, user_id, element_a, element_b)
    except Exception as e:
        logger.error(f"Error checking access to elements: {e}")
        raise e

    # Step 2: Query the recipe database for the element
    try:
        recipe = await check_recipe(uow, event_bus, element_a, element_b)
    except Exception as e:
        logger.error(f"Error checking recipe: {e}")
        raise e

    if recipe:
        # Step 3(a): Get the element from the database
        try:
            element = await get_element_from_db(uow, event_bus, recipe.result_id)
        except Exception as e:
            logger.error(f"Error getting element from database: {e}")
            raise e
    else:
        # Step 3(b): Querying the Gemini for the element & save to elements database
        try:
            element = await get_element_from_gemini(
                uow, event_bus, element_a, element_b
            )
        except Exception as e:
            logger.error(f"Error getting element from Gemini: {e}")
            raise e

    # Step 4: Save user progress
    try:
        await create_progress(user_id, element.object_id, uow, event_bus)
    except Exception as e:
        logger.error(f"Error creating progress: {e}")
        raise e

    return element


@craft_router.get(
    "/{user_id}/progress",
    name="Get user progress",
    response_model=list[ProgressBase],
    status_code=200,
    tags=["Progress"],
)
@inject
async def get_user_progress(
    user_id: Annotated[int, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow_factory: Annotated[
        Callable[[], UnitOfWork], Depends(Provide[Container.uow_factory])
    ],
) -> list[ProgressBase]:
    """Get user progress"""
    uow = uow_factory()
    try:
        progress = await fetch_progress(user_id, uow, event_bus)
        return progress
    except Exception as e:
        logger.error(f"Error fetching progress: {e}")
        raise e
