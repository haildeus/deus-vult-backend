from dependency_injector.wiring import Provide, inject
from pydantic_ai import Agent

from src import Container
from src.shared.base import BaseService
from src.shared.base_llm import VertexLLM


class CombinationService(BaseService):
    def __init__(self):
        super().__init__()

    @property
    def agent(self) -> Agent:
        return self.create_agent()

    @inject
    def create_agent(self, model_object: VertexLLM = Provide[Container.model]) -> Agent:
        return Agent(
            model=model_object.model,
            system_prompt="You're a helpful assistant that can help me create combinations of elements.",
        )
