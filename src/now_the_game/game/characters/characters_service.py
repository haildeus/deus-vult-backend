from src.now_the_game.game.characters.characters_model import character_model
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import CharacterTopics
from src.shared.events import Event


class CharactersService(BaseService):
    def __init__(self) -> None:
        super().__init__()
        self.model = character_model

    @EventBus.subscribe(CharacterTopics.CHARACTER_CREATE)
    async def on_create_character(self, event: Event) -> None:
        pass

    @EventBus.subscribe(CharacterTopics.CHARACTER_FETCH)
    async def on_fetch_character(self, event: Event) -> None:
        pass
