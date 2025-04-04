from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings

from src.agents.agents_interfaces import IAgentEvent
from src.shared.event_registry import GlifTopics
from src.shared.events import EventPayload


class GlifGeneratorID(Enum):
    """
    The IDs of the Glif generators
    """

    MEDIEVAL_IMAGE_GEN = "cm1926mxf0006ekfvp3xr69da"
    TEST_PIC_GEN = "clgh1vxtu0011mo081dplq3xs"
    TEST_ECHO_GEN = "clozwqgs60013l80fkgmtf49o"


"""
CONFIG
"""


class GlifConfig(BaseSettings):
    api_key: str | None = None
    url: str = "https://simple-api.glif.app/"

    class Config:
        env_prefix = "GLIF_"
        extra = "ignore"
        env_file = ".env"

    @model_validator(mode="before")
    def validate_api_key(cls, values: dict[str, Any]) -> dict[str, Any]:
        if not values.get("api_key"):
            raise ValueError("api_key must be provided")
        return values

    @property
    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


"""
MODELS
"""


class GlifBody(BaseModel):
    id: str = Field(..., description="The ID of the Glif service")
    inputs: list[str] | dict[str, str] = Field(
        ..., description="The inputs for the Glif service"
    )


class GlifResponse(BaseModel):
    output: str = Field(..., description="The output of the Glif service")


"""
EVENTS
"""


class GlifQueryPayload(EventPayload):
    inputs: list[str] | dict[str, str]
    service_id: str | GlifGeneratorID


class GlifQueryEvent(IAgentEvent):
    topic: str = GlifTopics.QUERY.value
    payload: GlifQueryPayload  # type: ignore


class GlifResponseEvent(IAgentEvent):
    topic: str = GlifTopics.RESPONSE.value
    payload: GlifResponse  # type: ignore
