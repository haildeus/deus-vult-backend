from .. import Event, event_bus, logger
from .agents_exceptions import UnsupportedModelError
from .agents_schemas import (
    AgentQueryPayload,
    SupportedModels,
)


class AgentsService:
    def __init__(self):
        logger.debug("Initializing AgentsService")
        self.event_bus = event_bus
        logger.debug("AgentsService initialized")

    async def on_agent_query(self, event: Event) -> None:
        if not isinstance(event.payload, AgentQueryPayload):
            payload = AgentQueryPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.info(f"Received agent query: {payload}")

        if payload.model == SupportedModels.VERTEX:
            pass
        elif payload.model == SupportedModels.GEMINI:
            pass
        else:
            raise UnsupportedModelError(payload.model)

    async def get_glif_requesst(
        self, inputs: list[str], service_id: str = "clozwqgs60013l80fkgmtf49o"
    ):
        glif_payload = {
            "inputs": inputs,
            "service_id": service_id,
        }
        glif_topic = "agents.glif.query"
        event = Event.from_dict(glif_topic, glif_payload)
        return await self.event_bus.request(event)

    async def get_text_query(self, query: str, model: str) -> str:
        text_query_payload = {
            "query": query,
            "model": model,
        }
        text_query_topic = "agents.language_model.text.query"
        event = Event.from_dict(text_query_topic, text_query_payload)
        response = await self.event_bus.request(event)
        return response.payload.response

    async def get_multimodal_query(self, query: str, image: bytes, model: str) -> str:
        multimodal_query_payload = {
            "query": query,
            "image": image,
            "model": model,
        }
        multimodal_query_topic = "agents.language_model.multimodal.query"
        event = Event.from_dict(multimodal_query_topic, multimodal_query_payload)
        response = await self.event_bus.request(event)
        return response.payload.response
