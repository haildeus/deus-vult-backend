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
    payload: dict[str, Any] | EventPayload | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_dict(cls, topic: str, payload: dict[str, Any]) -> "Event":
        return cls(topic=topic, payload=payload)
