"""
This module contains the ElementsAgent class which is responsible for LLM-driven interactions
"""

import logging
from typing import cast

from fastapi import HTTPException
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from src.api.craft.elements.elements_prompts import (
    ELEMENTS_COMBINATION_EXAMPLES,
    ELEMENTS_COMBINATION_QUERY,
    ELEMENTS_COMBINATION_SYSTEM_PROMPT,
)
from src.api.craft.elements.elements_schemas import Element, ElementInput, ElementOutput
from src.shared.base import BaseService
from src.shared.base_llm import VertexLLM
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function

logger = logging.getLogger("deus-vult.api.craft")


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
                temperature=1,
                max_tokens=300,
            ),
            retries=3,
        )

    @EventBus.subscribe(ElementTopics.ELEMENT_COMBINATION)
    @async_traced_function
    async def handle_element_combination(self, event: Event) -> Element:
        payload = cast(ElementInput, event.extract_payload(event, ElementInput))

        try:
            assert payload.element_a
            assert payload.element_b
        except AssertionError as e:
            raise HTTPException(status_code=400, detail="Invalid elements") from e

        result = await self.combine_elements(payload)
        return result

    @async_traced_function
    async def combine_elements(self, input: ElementInput) -> Element:
        try:
            input_string = f"Input:\n{input.model_dump_json()}"

            query_string = f"""
            {ELEMENTS_COMBINATION_QUERY}

            {ELEMENTS_COMBINATION_EXAMPLES}

            {input_string}
            """
            response = await self.agent_object.run(query_string)
            return_value = response.data

            logger.debug("Elements combination agent response: %s", return_value)
        except Exception as e:
            logger.error("Error running elements combination agent: %s", e)
            raise e

        response_object = ElementOutput.model_validate(return_value)
        return response_object.result
