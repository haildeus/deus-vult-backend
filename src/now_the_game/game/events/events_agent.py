from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from src.now_the_game.game.events.events_prompts import EVENTS_SYSTEM_PROMPT
from src.now_the_game.game.events.events_schemas import EventAgentOutput
from src.shared.base import BaseService
from src.shared.base_llm import VertexLLM
from src.shared.event_bus import EventBus
from src.shared.event_registry import EventTopics
from src.shared.events import Event


class EventsAgent(BaseService):
    def __init__(self, provider: VertexLLM):
        super().__init__()
        self.provider = provider

        # -- creating an agent --
        self.agent_object = Agent(
            name="Events Agent",
            model=self.provider.model,
            system_prompt=EVENTS_SYSTEM_PROMPT,
            result_type=EventAgentOutput,
            model_settings=ModelSettings(
                temperature=0.8,
                max_tokens=100,
            ),
            retries=3,
        )

    @EventBus.subscribe(EventTopics.EVENT_AGENT_CREATE.value)
    async def on_create_event(self, event: Event) -> None:
        pass
