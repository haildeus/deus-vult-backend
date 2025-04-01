from src import Event, event_bus
from src.now_the_game import logger
from src.now_the_game.agents.agents_exceptions import UnsupportedModelError
from src.now_the_game.agents.agents_schemas import AgentQueryPayload, SupportedModels
from src.shared.event_registry import GlifTopics, LanguageModelTopics


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
        event = Event.from_dict(GlifTopics.QUERY.value, glif_payload)
        return await self.event_bus.request(event)

    async def get_text_query(self, query: str, model: str) -> str:
        text_query_payload = {
            "query": query,
            "model": model,
        }
        event = Event.from_dict(
            LanguageModelTopics.TEXT_QUERY.value, text_query_payload
        )
        response = await self.event_bus.request(event)
        return response.payload.response

    async def get_multimodal_query(self, query: str, image: bytes, model: str) -> str:
        multimodal_query_payload = {
            "query": query,
            "image": image,
            "model": model,
        }
        event = Event.from_dict(
            LanguageModelTopics.MULTI_MODAL_QUERY.value, multimodal_query_payload
        )
        response = await self.event_bus.request(event)
        return response.payload.response
