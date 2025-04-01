from enum import Enum

from src import BaseService, Event, EventPayload, event_bus
from src.now_the_game import logger
from src.now_the_game.agents.agents_interfaces import IAgentEvent
from src.now_the_game.agents.language_models.vertex import vertex
from src.shared.event_registry import LanguageModelTopics

EVENT_BUS_PREFIX = "agents.language_model"

"""
ENUMS
"""


class SupportedLanguageModels(Enum):
    VERTEX = "vertex"
    GEMINI = "gemini"


"""
MODELS
"""


class TextResponsePayload(EventPayload):
    response: str


class MultiModalResponsePayload(EventPayload):
    response: str


"""
EVENTS
"""


class LanguageModelPayload(EventPayload):
    model: SupportedLanguageModels


class TextQueryPayload(LanguageModelPayload):
    query: str


class MultiModalQueryPayload(LanguageModelPayload):
    query: str
    image: bytes


class TextQueryEvent(IAgentEvent):
    topic: str = LanguageModelTopics.TEXT_QUERY.value
    payload: TextQueryPayload  # type: ignore


class MultiModalQueryEvent(IAgentEvent):
    topic: str = LanguageModelTopics.MULTI_MODAL_QUERY.value
    payload: MultiModalQueryPayload  # type: ignore


class TextResponseEvent(IAgentEvent):
    topic: str = LanguageModelTopics.TEXT_RESPONSE.value
    payload: TextResponsePayload  # type: ignore


class MultiModalResponseEvent(IAgentEvent):
    topic: str = LanguageModelTopics.MULTI_MODAL_RESPONSE.value
    payload: MultiModalResponsePayload  # type: ignore


"""
SERVICE
"""


class LanguageModelService(BaseService):
    def __init__(self):
        super().__init__()

    @event_bus.subscribe(LanguageModelTopics.TEXT_QUERY.value)
    async def on_text_query(self, event: Event):
        if not isinstance(event.payload, TextQueryPayload):
            payload = TextQueryPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        selected_model = payload.model
        logger.debug(f"Selected model: {selected_model}")

        # TODO: Figure out candidates and parts for Vertex. How does it work?
        if selected_model == SupportedLanguageModels.VERTEX:
            logger.debug("Generating text with Vertex")
            response = await vertex.generate_text(payload.query)

            response_text = response.candidates[0].content.parts[0].text
            response = TextResponseEvent(
                payload=TextResponsePayload(response=response_text)
            )
            logger.debug(f"Text response: {response}")
            return response

        elif selected_model == SupportedLanguageModels.GEMINI:
            raise NotImplementedError("Gemini text model is not implemented yet")

    @event_bus.subscribe(LanguageModelTopics.MULTI_MODAL_QUERY.value)
    async def on_multi_modal_query(self, event: Event):
        if not isinstance(event.payload, MultiModalQueryPayload):
            payload = MultiModalQueryPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        selected_model = payload.model
        logger.debug(f"Selected model: {selected_model}")
        if selected_model == SupportedLanguageModels.VERTEX:
            logger.debug("Generating multimodal with Vertex")
            response = await vertex.generate_multimodal(payload.query, payload.image)
            response_text = response.candidates[0].content.parts[0].text
            response = MultiModalResponseEvent(
                payload=MultiModalResponsePayload(response=response_text)
            )
            logger.debug(f"Multimodal response: {response}")
            return response
        elif selected_model == SupportedLanguageModels.GEMINI:
            raise NotImplementedError("Gemini visual model is not implemented yet")
