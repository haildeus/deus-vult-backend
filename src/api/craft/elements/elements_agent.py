from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from src.api import logger, logger_wrapper
from src.api.craft.elements.elements_prompts import ELEMENTS_COMBINATION_SYSTEM_PROMPT
from src.api.craft.elements.elements_schemas import (
    CombineElementsEventResponse,
    ElementInput,
    ElementOutput,
)
from src.shared.base import BaseService
from src.shared.base_llm import VertexLLM
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics
from src.shared.events import Event


class ElementsAgent(BaseService):
    def __init__(self, provider: VertexLLM):
        super().__init__()
        self.provider = provider
        # -- creating an agent --

        self.agent_object = Agent(
            name="Elements Combination Agent",
            model=self.provider.model,
            system_prompt=ELEMENTS_COMBINATION_SYSTEM_PROMPT,
            result_type=ElementOutput,
            model_settings=ModelSettings(
                temperature=0.8,
                max_tokens=100,
            ),
            retries=3,
        )

    @EventBus.subscribe(ElementTopics.ELEMENT_COMBINATION.value)
    @logger_wrapper.log_debug
    async def handle_element_combination(self, event: Event):
        if not isinstance(event.payload, ElementInput):
            payload = ElementInput(**event.payload)  # type: ignore
        else:
            payload = event.payload

        result = await self.combine_elements(payload)
        return CombineElementsEventResponse(payload=result, topic=ElementTopics.ELEMENT_COMBINATION_RESPONSE.value)
    

    async def combine_elements(self, input: ElementInput) -> ElementOutput:
        try:
            response = await self.agent_object.run(
                f"**Input:**\n{input.model_dump_json()}"
            )
            return_value = response.data
        except Exception as e:
            logger.error(f"Error running elements combination agent: {e}")
            raise e
        
        return ElementOutput.model_validate(return_value)
