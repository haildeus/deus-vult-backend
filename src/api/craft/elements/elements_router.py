from fastapi import APIRouter, Path

from src import Event, event_bus
from src.api import logger
from src.api.core.database import api_db
from src.api.core.interfaces import SuccessResponse

elements_router = APIRouter()


@elements_router.get(
    "/elements",
    name="Get all elements",
    response_model=SuccessResponse,
    status_code=200,
)
async def get_element_all() -> SuccessResponse:
    """Get all elements"""
    logger.debug("Getting all elements")

    async with api_db.session() as session:
        payload_example = {"db": session}
        event = Event(
            topic="craft.elements.get",
            payload=payload_example,
        )
        response = await event_bus.request(event)
        logger.debug(f"Element response: {response}")

    return SuccessResponse(message="Elements fetched successfully", data=response)


@elements_router.post(
    "/elements",
    name="Create a new element",
    response_model=SuccessResponse,
    status_code=201,
)
async def create_element(entity: str) -> SuccessResponse:
    """Create a new element"""
    logger.debug("Creating new element")

    async with api_db.session() as session:
        # Create payload
        payload_example = {"entity": entity, "db_session": session}
        # Create event
        event = Event(
            topic="craft.elements.created",
            payload=payload_example,
        )
        # Send event to event bus
        await event_bus.publish_and_wait(event)
        # Flush session
        await session.flush()
        logger.debug("Element created")

    return SuccessResponse(
        message="Element created", data={"message": "Element created"}
    )


@elements_router.get(
    "/elements/{element_id}",
    name="Get an element by ID",
    response_model=SuccessResponse,
    status_code=200,
)
async def get_element(
    element_id: int = Path(..., description="The ID of the element"),
) -> SuccessResponse:
    """Get an element by ID"""
    logger.debug(f"Getting element with ID: {element_id}")

    async with api_db.session() as session:
        payload_example = {"element_id": element_id, "db": session}
        event = Event(
            topic="craft.elements.get",
            payload=payload_example,
        )
        response = await event_bus.request(event)
        logger.debug(f"Element response: {response}")

    return SuccessResponse(message="Element fetched successfully", data=response)
