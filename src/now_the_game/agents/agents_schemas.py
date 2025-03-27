from enum import Enum

from src import EventPayload
from src.now_the_game.agents.agents_interfaces import IAgentEvent


class SupportedModels(Enum):
    VERTEX = "vertex"
    GEMINI = "gemini"


class AgentQueryPayload(EventPayload):
    query: str
    model: SupportedModels


class AgentQueryEvent(IAgentEvent):
    topic: str = "agents.query"
    payload: AgentQueryPayload  # type: ignore
