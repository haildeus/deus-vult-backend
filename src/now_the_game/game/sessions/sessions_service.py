from src.now_the_game.game.sessions.sessions_model import session_model
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import SessionTopics
from src.shared.events import Event


class SessionsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = session_model

    @EventBus.subscribe(SessionTopics.SESSION_CREATE.value)
    async def on_create_session(self, event: Event) -> None:
        pass

    @EventBus.subscribe(SessionTopics.SESSION_FETCH.value)
    async def on_fetch_session(self, event: Event) -> None:
        pass
