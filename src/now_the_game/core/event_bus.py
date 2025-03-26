from abc import ABC, abstractmethod
from asyncio import gather
from collections.abc import Callable

from .config import Config, EventBusType, config
from .events import Event


class EventBusInterface(ABC):
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event"""
        pass

    @abstractmethod
    def subscribe(
        self, event_type: type[Event], callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type"""
        pass


class EventBus(EventBusInterface):
    def __init__(self):
        self._subscribers: dict[type[Event], list[Callable[[Event], None]]] = {}

    def subscribe(
        self, event_type: type[Event], callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event: Event) -> None:
        """Publish an event"""
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        await gather(*[handler(event) for handler in handlers])  # type: ignore


def get_event_bus(config_obj: Config) -> EventBusInterface:
    if config_obj.event_bus == EventBusType.LOCAL:
        return EventBus()
    else:
        raise ValueError(f"Unsupported event bus type: {config_obj.event_bus}")


# singleton
event_bus = get_event_bus(config)
