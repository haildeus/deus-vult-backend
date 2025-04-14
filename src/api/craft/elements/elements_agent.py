"""
This module contains the ElementsAgent class which is responsible for LLM-driven interactions
"""

from typing import cast

from fastapi import HTTPException
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from src.api import logger
from src.api.craft.elements.elements_prompts import ELEMENTS_COMBINATION_SYSTEM_PROMPT
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementBaseInput,
    ElementInput,
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
            result_type=Element,
            model_settings=ModelSettings(
                temperature=0.8,
                max_tokens=100,
            ),
            retries=3,
        )

    @EventBus.subscribe(ElementTopics.ELEMENT_COMBINATION)
    async def handle_element_combination(self, event: Event) -> Element:
        payload = cast(ElementInput, event.extract_payload(event, ElementInput))

        try:
            assert payload.element_a
            assert payload.element_b
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid elements") from e

        result = await self.combine_elements(payload)
        return result

    async def combine_elements(self, input: ElementInput) -> Element:
        try:
            response = await self.agent_object.run(
                f"**Input:**\n{input.model_dump_json()}"
            )
            return_value = response.data
        except Exception as e:
            logger.error(f"Error running elements combination agent: {e}")
            raise e

        return Element.model_validate(return_value)
