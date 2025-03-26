"""
Events are used to communicate between different parts of the application.

They are published to the event bus and subscribed to by the event bus.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    class Config:
        arbitrary_types_allowed = True


class Event(BaseModel):
    topic: str
    payload: EventPayload | dict[str, Any] | None
    timestamp: datetime = Field(default_factory=datetime.now)
