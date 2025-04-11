from collections.abc import Callable
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src import Container
from src.api import logger
from src.api.core.dependencies import validate_init_data
from src.api.craft.craft_orchestration import (
    fetch_progress,
    orchestrate_element_combination,
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
    """
    Combines two elements. Checks for existing recipes or generates a new one.
    Updates user progress atomically.
    """
    logger.debug(
        f"Combining elements: {element_a.name} ({element_a.object_id}) + "
        f"{element_b.name} ({element_b.object_id}) for user {user_id}"
    )
    try:
        assert element_a and element_a.object_id
        assert element_b and element_b.object_id
        assert (
            element_a.object_id != element_b.object_id
        )  # Prevent combining element with itself? Adjust if needed.
    except AssertionError as e:
        logger.error(
            f"Invalid elements provided for combination: A={element_a}, B={element_b}"
        )
        raise HTTPException(
            status_code=400, detail="Invalid elements provided for combination."
        ) from e

    uow = uow_factory()

    try:
        # Call the single orchestrator function
        result_element = await orchestrate_element_combination(
            user_id=user_id,
            element_a_id=element_a.object_id,
            element_b_id=element_b.object_id,
            uow=uow,
            event_bus=event_bus,
        )
        logger.info(
            f"Combination successful for user {user_id}. Result: {result_element.name} "
            f"({result_element.object_id})"
        )
        return result_element
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(
            f"Unexpected error during element combination orchestration: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during combination."
        ) from e


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
        # Assuming fetch_progress handles caching and fetching logic
        progress = await fetch_progress(user_id, uow, event_bus)
        return progress
    except Exception as e:
        logger.error(f"Error fetching progress for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to fetch user progress."
        ) from e
