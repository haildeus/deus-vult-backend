import logging
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src import Container
from src.api.core.dependencies import validate_init_data
from src.api.craft.craft_orchestration import (
    fetch_init_elements,
    fetch_progress,
    orchestrate_element_combination,
)
from src.api.craft.elements.elements_schemas import ElementApiInput, ElementResponse
from src.api.craft.progress.progress_schemas import ProgressResponse
from src.shared.cache import disk_cache
from src.shared.event_bus import EventBus
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork

logger = logging.getLogger("deus-vult.api.craft")

craft_router = APIRouter(prefix="/craft")


@craft_router.get(
    "/elements/init",
    name="Get initial elements",
    response_model=list[ElementResponse],
    status_code=200,
    tags=["Elements"],
)
@disk_cache(
    key_params=["user_id"],
    ttl=60 * 60 * 24,
)
@async_traced_function
@inject
async def get_init_elements(
    user_id: Annotated[int, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow: Annotated[UnitOfWork, Depends(Provide[Container.uow_factory])],
) -> list[ElementResponse]:
    """Get initial elements"""

    _ = user_id

    try:
        return await fetch_init_elements(uow, event_bus)
    except Exception as e:
        raise e


@craft_router.post(
    "/elements/combine",
    name="Combining elements",
    response_model=ElementResponse,
    status_code=201,
    tags=["Elements"],
)
@disk_cache(
    key_params=[
        "user_id",
        "element_ids.object_id_a",
        "element_ids.object_id_b",
    ],
    ttl=60 * 60 * 24,
)
@async_traced_function
@inject
async def combine_elements(
    user_id: Annotated[int, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow: Annotated[UnitOfWork, Depends(Provide[Container.uow_factory])],
    element_ids: ElementApiInput,
) -> ElementResponse:
    """
    Combines two elements. Checks for existing recipes or generates a new one.
    Updates user progress atomically.
    """
    logger.debug(
        "Combining elements: %s + %s",
        element_ids.object_id_a,
        element_ids.object_id_b,
    )
    try:
        assert element_ids.object_id_a
        assert element_ids.object_id_b
    except AssertionError as e:
        logger.error(
            "Invalid elements provided for combination: "
            "A=%s, B=%s",
            element_ids.object_id_a,
            element_ids.object_id_b,
        )
        raise HTTPException(
            status_code=400, detail="Invalid elements provided for combination."
        ) from e

    try:
        # Call the single orchestrator function
        result_element: ElementResponse = await orchestrate_element_combination(
            user_id=user_id,
            element_a_id=element_ids.object_id_a,
            element_b_id=element_ids.object_id_b,
            uow=uow,
            event_bus=event_bus,
        )
        logger.info(
            "Combination successful for user %s. Result: %s "
            "(%s)",
            user_id,
            result_element.name,
            result_element.object_id,
        )
        return result_element
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(
            "Unexpected error during element combination orchestration: %s",
            e,
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during combination."
        ) from e


@craft_router.get(
    "/progress",
    name="Get user progress",
    response_model=list[ProgressResponse],
    status_code=200,
    tags=["Progress"],
)
@async_traced_function
@inject
async def get_user_progress(
    user_id: Annotated[int, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow: Annotated[UnitOfWork, Depends(Provide[Container.uow_factory])],
) -> list[ProgressResponse]:
    """Get user progress"""
    try:
        # Assuming fetch_progress handles caching and fetching logic
        progress = await fetch_progress(user_id, uow, event_bus)
        return progress
    except Exception as e:
        logger.exception("Error fetching progress for user %s: %s", user_id, e)
        raise HTTPException(
            status_code=500, detail="Failed to fetch user progress."
        ) from e
