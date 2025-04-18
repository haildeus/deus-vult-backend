import logging
from enum import Enum
from typing import Any, cast

import httpx
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings

from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import GlifTopics
from src.shared.events import Event, EventPayload
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.glif-service")

"""
ENUMS
"""


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
PAYLOADS
"""


class GlifQueryPayload(EventPayload):
    inputs: list[str] | dict[str, str]
    service_id: str | GlifGeneratorID


"""
SERVICE
"""


class GlifService(BaseService):
    @EventBus.subscribe(GlifTopics.QUERY)
    @async_traced_function
    async def on_glif_query(self, event: Event) -> GlifResponse:
        payload = cast(GlifQueryPayload, Event.extract_payload(event, GlifQueryPayload))
        logger.debug("Glif query: %s", payload)
        response = await self.glif_request(payload.service_id, payload.inputs)
        logger.debug("Glif response %s", response)
        return response

    @staticmethod
    @async_traced_function
    async def glif_request(
        service_id: GlifGeneratorID | str,
        inputs: list[str] | dict[str, str],
    ) -> GlifResponse:
        """
        Takes an ID and inputs and uses Glif to generate an image:
        - Accesses API endpoint: https://simple-api.glif.app
        - Uses Bearer token for authentication
        - Sends POST request to the API
        - Returns a GlifResponse object

        Args:
            service_id: The ID of the Glif service or a GlifGeneratorID enum
            inputs: The inputs for the Glif service

        Returns:
            A GlifResponse object containing the output of the Glif service
        """
        try:
            assert service_id
            assert isinstance(service_id, GlifGeneratorID) or isinstance(
                service_id, str
            )
            assert inputs
            assert isinstance(inputs, list) or isinstance(inputs, dict)
            assert len(inputs) > 0
        except AssertionError as e:
            raise ValueError("Invalid input params") from e

        if isinstance(service_id, GlifGeneratorID):
            service_id = service_id.value

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GlifConfig().url,
                json=GlifBody(
                    id=service_id,
                    inputs=inputs,
                ).model_dump(),
                headers=GlifConfig().auth_header,
                timeout=30,
            )

            return GlifResponse(**response.json())

    async def glif_mediaeval_request(self, input_: str) -> GlifResponse:
        """
        Takes an input string and uses Glif to generate a mediaeval-styled image

        Args:
            input_: The input string to generate an image for, less than 300 characters

        Returns:
            A GlifResponse object containing the output of the Glif service
        """
        return await self.glif_request(GlifGeneratorID.MEDIEVAL_IMAGE_GEN, [input_])

    async def test_glif_echo(self):
        response = await self.glif_request(
            GlifGeneratorID.TEST_ECHO_GEN, ["Hello, world!"]
        )
        logger.info("Echo response: %s", response)

    async def test_glif_pic(self):
        response = await self.glif_request(
            GlifGeneratorID.TEST_PIC_GEN, ["cute friendly oval shaped bot friend"]
        )
        logger.info("Echo response: %s", response)
