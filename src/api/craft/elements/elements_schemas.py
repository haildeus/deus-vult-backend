from typing import Any

from pydantic import model_validator
from sqlmodel import Field

from src.api.craft.craft_interfaces import ICraftElementEvent
from src.shared.base import BaseSchema
from src.shared.event_registry import ElementTopics
from src.shared.events import EventPayload

"""
MODELS
"""


class Element(EventPayload):
    """
    Base model for an element class.

    Attributes:
        - name: The name of the element
        - emoji: The emoji representing the element.
    """

    name: str = Field(max_length=100, description="The name of the element")
    emoji: str = Field(max_length=10, description="The emoji representing the element")


class CreateElement(Element):
    pass


class FetchElement(EventPayload):
    element_id: int | None = None
    name: str | None = None

    @model_validator(mode="before")
    def validate_payload(cls, values: dict[str, Any]) -> dict[str, Any]:
        if values.get("element_id") and values.get("name"):
            raise ValueError("Only one of element_id or name must be provided")
        return values


"""
PAYLOADS
"""


class CreateElementPayload(CreateElement):
    pass


class FetchElementPayload(FetchElement):
    pass


class FetchElementResponsePayload(EventPayload):
    elements: list["ElementBase"]


"""
EVENTS
"""


class CreateElementEvent(ICraftElementEvent):
    topic: str = ElementTopics.ELEMENT_CREATE.value
    payload: CreateElementPayload  # type: ignore


class FetchElementEvent(ICraftElementEvent):
    topic: str = ElementTopics.ELEMENT_FETCH.value
    payload: FetchElementPayload  # type: ignore


class FetchElementEventResponse(ICraftElementEvent):
    topic: str = ElementTopics.ELEMENT_FETCH_RESPONSE.value
    payload: FetchElementResponsePayload  # type: ignore


"""
TABLES
"""


class ElementBase(BaseSchema):
    name: str = Field(index=True, unique=True, max_length=100)
    emoji: str = Field(max_length=10)


class ElementTable(ElementBase, table=True):
    __tablename__ = "elements"  # type: ignore
