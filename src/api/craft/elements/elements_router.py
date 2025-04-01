from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src import Event, event_bus
from src.api import logger, logger_wrapper
from src.api.core.database import api_db
from src.api.core.dependencies import validate_init_data
from src.api.core.interfaces import SuccessResponse
from src.api.craft.elements.elements_schemas import CreateElement, ElementTopics

elements_router = APIRouter()


@elements_router.get(
    "/elements",
    name="Get elements",
    response_model=SuccessResponse,
    status_code=200,
)
@logger_wrapper.log_debug
async def get_elements(
    init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    element_id: int | None = Query(None, description="The ID of the element"),
    name: str | None = Query(None, description="The name of the element"),
) -> SuccessResponse:
    """Get elements"""
    logger.debug("Getting elements")
    if element_id and name:
        raise HTTPException(
            status_code=400, detail="Only one of element_id or name must be provided"
        )

    async with api_db.session() as session:
        payload_example = {
            "element_id": element_id,
            "name": name,
            "db_session": session,
        }
        event = Event.from_dict(ElementTopics.ELEMENT_FETCH.value, payload_example)
        response = await event_bus.request(event)
        logger.debug(f"Element response: {response.payload.elements}")

    return SuccessResponse(
        message="Elements fetched successfully", data=response.payload.elements
    )


@elements_router.post(
    "/elements",
    name="Create a new element",
    response_model=SuccessResponse,
    status_code=201,
)
@logger_wrapper.log_debug
async def create_element(
    init_data: Annotated[dict[str, str] | None, Depends(validate_init_data)],
    element: CreateElement,
) -> SuccessResponse:
    """Create a new element"""
    logger.debug(f"Creating new element: {element}")

    async with api_db.session() as session:
        # Create payload
        payload_example = {
            "name": element.name,
            "emoji": element.emoji,
            "db_session": session,
        }
        # Create event
        event = Event.from_dict(ElementTopics.ELEMENT_CREATE.value, payload_example)
        # Send event to event bus
        await event_bus.publish_and_wait(event)
        # Flush session
        await session.flush()
        logger.debug("Element created")

    return SuccessResponse(
        message="Element created", data={"message": "Element created"}
    )
