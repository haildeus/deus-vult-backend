from typing import Any

from pydantic_ai import Agent

from .prompts.system_prompts import DEFAULT_SYSTEM_PROMPT
from .providers.base import ProviderBase


class TextAgentModel:
    """
    TextAgentModel handles the creation of LLM-driven agents.
    """

    def __init__(
        self, provider: ProviderBase, system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ):
        self.provider = provider
        self.agent = Agent(
            model=self.provider.model,
            name=self.provider.provider_name,
            system_prompt=system_prompt,
        )

    async def embed(self, content: str) -> list[float]:
        return await self.provider.embed_content(content)

    async def run(self, query: str, **kwargs: Any) -> str:
        request = await self.agent.run(query, **kwargs)
        return request.data


class ImageAgentModel:
    """
    ImageAgentModel handles the creation of image-based agents.
    """

    raise NotImplementedError("ImageAgentModel is not implemented yet")
