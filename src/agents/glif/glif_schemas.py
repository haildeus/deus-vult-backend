import os
from enum import Enum

from google.auth import default as google_default_credentials  # type: ignore
from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings

from src.agents import logger
from src.agents.agents_interfaces import IAgentEvent
from src.shared.config import get_secret
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
    # GLIF VARIABLES
    url: str = "https://simple-api.glif.app/"

    # GOOGLE CLOUD VARIABLES
    google_project_id: str | None = Field(None, validation_alias="GOOGLE_CLOUD_PROJECT")
    api_key_secret_id: str | None = Field(
        None, validation_alias="GLIF_API_KEY_SECRET_ID"
    )

    class Config:
        env_prefix = "GLIF_"
        extra = "ignore"
        env_file = ".env"

    @computed_field(return_type=str)
    @property
    def api_key(self) -> str:
        """Fetch GLIF_API_KEY from Secret Manager or local environment."""
        if not self.api_key_secret_id:
            local_api_key = os.environ.get("GLIF_API_KEY")
            if local_api_key:
                logger.warning(
                    "Using GLIF_API_KEY env var for local dev. "
                    "Set GLIF_API_KEY_SECRET_ID for deployed environments."
                )
                return local_api_key
        if not self.google_project_id:
            # Auto-detect project ID
            try:
                _creds, detected_project_id = google_default_credentials()  # type: ignore
                if detected_project_id:
                    self.google_project_id = detected_project_id
                else:
                    raise ValueError("Could not auto-detect Google Cloud Project ID.")
            except Exception as e:
                raise ValueError(
                    f"Failed to get Google Cloud Project ID for secret fetching: {e}"
                ) from e
        logger.debug(
            f"Attempting to fetch secret '{self.api_key_secret_id}' "
            f"from project '{self.google_project_id}'"  # type: ignore
        )
        fetched_api_key = get_secret(self.google_project_id, self.api_key_secret_id)  # type: ignore
        if fetched_api_key is None:
            raise ValueError(
                f"Failed to fetch API key from Secret Manager "
                f"(Secret ID: {self.api_key_secret_id}). Check logs and permissions."
            )
        return fetched_api_key

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
