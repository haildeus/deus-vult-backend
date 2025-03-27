from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from src import BaseSchema, EventPayload
from src.api.craft.craft_interfaces import ICraftElementEvent

"""
CONSTANTS
"""

EVENT_BUS_PREFIX = "api.craft.elements"

"""
ENUMS
"""


class ElementTopics(Enum):
    ELEMENT_CREATED = f"{EVENT_BUS_PREFIX}.fetch"
    ELEMENT_GET = f"{EVENT_BUS_PREFIX}.get"
    ELEMENT_GET_RESPONSE = f"{EVENT_BUS_PREFIX}.get.response"


"""
MODELS
"""


class ElementCreatedPayload(EventPayload):
    pass


class ElementGetPayload(EventPayload):
    element_id: int | None = None
    db: AsyncSession


class ElementGetResponsePayload(EventPayload):
    elements: list["ElementBase"]


"""
EVENTS
"""


class ElementCreatedEvent(ICraftElementEvent):
    topic: str = ElementTopics.ELEMENT_CREATED.value
    payload: ElementCreatedPayload  # type: ignore


class ElementGetEvent(ICraftElementEvent):
    topic: str = ElementTopics.ELEMENT_GET.value
    payload: ElementGetPayload  # type: ignore


class ElementGetResponse(EventPayload):
    topic: str = ElementTopics.ELEMENT_GET_RESPONSE.value
    payload: ElementGetResponsePayload  # type: ignore


"""
TABLES
"""


class ElementBase(BaseSchema):
    pass


class ElementTable(ElementBase, table=True):
    __tablename__ = "elements"  # type: ignore
