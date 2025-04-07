from src.api.craft.progress.progress_model import progress_model
from src.api.craft.progress.progress_schemas import CreateProgress, FetchProgress
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import ProgressTopics
from src.shared.events import Event


# TODO: finish implementing the service
class ProgressService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = progress_model

    @EventBus.subscribe(ProgressTopics.PROGRESS_CREATE.value)
    async def on_create_progress(self, event: Event) -> None:
        if not isinstance(event.payload, CreateProgress):
            payload = CreateProgress(**event.payload)  # type: ignore
        else:
            payload = event.payload

        raise NotImplementedError

    @EventBus.subscribe(ProgressTopics.PROGRESS_FETCH.value)
    async def on_fetch_progress(self, event: Event) -> None:
        if not isinstance(event.payload, FetchProgress):
            payload = FetchProgress(**event.payload)  # type: ignore
        else:
            payload = event.payload

        raise NotImplementedError
