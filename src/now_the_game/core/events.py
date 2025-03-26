from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)


class TelegramEvent(Event):
    pass


class AgentEvent(Event):
    pass


class GameEvent(Event):
    pass
