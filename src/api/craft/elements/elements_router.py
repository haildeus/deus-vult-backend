from collections.abc import Callable
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query

from src import Container
from src.api import logger, logger_wrapper
from src.api.core.dependencies import validate_init_data
from src.api.core.interfaces import SuccessResponse
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementInput,
    ElementOutput,
    ElementTopics,
)
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import UnitOfWork

elements_router = APIRouter()


@elements_router.get(
    "/elements",
    name="Get elements",
    response_model=SuccessResponse,
    status_code=200,
    tags=["Elements"],
)
@inject
@logger_wrapper.log_debug
async def get_elements(
    init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    uow_factory: Annotated[
        Callable[[], UnitOfWork], Depends(Provide[Container.uow_factory])
    ],
    element_id: int | None = Query(None, description="The ID of the element"),
    name: str | None = Query(None, description="The name of the element"),
) -> SuccessResponse:
    """Get elements"""
    logger.debug("Getting elements")
    if element_id and name:
        raise HTTPException(
            status_code=400, detail="Only one of element_id or name must be provided"
        )
    uow = uow_factory()

    async with uow.start():
        payload = {
            "element_id": element_id,
            "name": name,
        }
        event = Event.from_dict(ElementTopics.ELEMENT_FETCH.value, payload)
        response = await event_bus.request(event)
        logger.debug(f"Element response: {response.payload.elements}")

    return SuccessResponse(
        message="Elements fetched successfully", data=response.payload.elements
    )

@elements_router.post(
    "/elements/combine",
    name="Combining elements",
    response_model=SuccessResponse,
    status_code=201,
    tags=["Elements"],
)
@inject
@logger_wrapper.log_debug
async def combine_elements(
    #init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    event_bus: Annotated[EventBus, Depends(Provide[Container.event_bus])],
    element_a: Element,
    element_b: Element,
) -> SuccessResponse:
    """Combine elements"""
    logger.debug(f"Combining elements: {element_a} and {element_b}")
    try:
        assert element_a
        assert element_b
    except AssertionError as e:
        raise HTTPException(status_code=400, detail="Invalid elements") from e
    
    elements_input = ElementInput(element_a=element_a, element_b=element_b)
    event = Event.from_dict(ElementTopics.ELEMENT_COMBINATION.value, elements_input.model_dump())
    response = await event_bus.request(event)
    logger.debug(f"Element response: {response.payload.result}")

    return SuccessResponse(
        message="Elements combined successfully", data=response.payload.result
    )
