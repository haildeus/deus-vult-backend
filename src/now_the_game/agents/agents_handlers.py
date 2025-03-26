"""Agents handlers module"""

from src.now_the_game.agents.language_models.language_model_service import (
    LanguageModelService,
)
from src.now_the_game.agents.tools.glif import GlifService


class AgentsHandlers:
    def __init__(self):
        self.glif_service = GlifService()
        self.language_model_service = LanguageModelService()
