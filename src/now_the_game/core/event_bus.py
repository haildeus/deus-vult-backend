"""
The event bus is used to communicate between different parts of the application.

It is a singleton that is used to publish and subscribe to events.
"""

import uuid
from abc import ABC, abstractmethod
from asyncio import Task, create_task, gather
from collections.abc import Callable, Coroutine
from inspect import isawaitable
from typing import Any, TypeVar

from .config import Config, EventBusType
from .events import Event
from .logging import logger

E = TypeVar("E", bound=Event)
EventHandler = Callable[[E], None | Coroutine[Any, Any, None]]


class EventBusInterface(ABC):
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """Publish an event"""
        pass

    @abstractmethod
    def subscribe(self, event_type: type[E], callback: EventHandler[E]) -> None:
        """Subscribe to an event type"""
        pass

    @abstractmethod
    def get_subscriber_count(self, event_type: type[Event]) -> int:
        """Get the number of subscribers for an event type"""
        pass

    @abstractmethod
    async def publish_and_wait(self, event: Event) -> None:
        """Publish an event and wait for all handlers to complete"""
        pass


class EventBus(EventBusInterface):
    def __init__(self):
        self._subscribers: dict[type[Event], list[EventHandler[Any]]] = {}
        self._topic_subscribers: dict[str, list[EventHandler[Any]]] = {}
        self._event_tasks: dict[str, set[Task[Any]]] = {}

    def subscribe_to_topic(
        self, event_type: type[E], callback: Callable[[Event], Any]
    ) -> None:
        """Subscribe to all events of a specific topic"""
        topic = event_type.topic

        if topic not in self._topic_subscribers:
            self._topic_subscribers[topic] = []
        self._topic_subscribers[topic].append(callback)

    def subscribe(self, event_type: type[E], callback: EventHandler[E]) -> None:
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event: Event) -> None:
        """Publish an event to type subscribers and topic subscribers"""
        logger.debug(f"Publishing event: {event}")

        # Type-based subscribers
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        # Topic-based subscribers
        topic_handlers = self._topic_subscribers.get(event.topic, [])

        # Combine handlers
        all_handlers = handlers + topic_handlers

        if not all_handlers:
            return

        coros: list[Coroutine[Any, Any, None]] = []
        for handler in all_handlers:
            result = handler(event)
            if isawaitable(result):
                coros.append(result)

        if coros:
            await gather(*coros)

    async def publish_and_wait(self, event: Event) -> None:
        """Publish an event and wait for all handlers to complete"""
        logger.debug(f"Publishing event and waiting: {event}")

        # Type-based subscribers
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])

        # Topic-based subscribers
        topic_handlers = self._topic_subscribers.get(event.topic, [])

        # Combine handlers
        all_handlers = handlers + topic_handlers

        if not all_handlers:
            return

        # Create a unique ID for this event instance
        event_id = str(uuid.uuid4())
        self._event_tasks[event_id] = set()

        # Create tasks for each handler
        for handler in all_handlers:
            logger.debug(f"Creating task for handler: {handler}")
            result = handler(event)
            if isawaitable(result):
                task = create_task(result)
                self._event_tasks[event_id].add(task)

        # Wait for all tasks to complete
        if self._event_tasks[event_id]:
            logger.debug(f"Waiting for {len(self._event_tasks[event_id])} tasks")
            await gather(*self._event_tasks[event_id])

        # Clean up
        del self._event_tasks[event_id]
        logger.debug(f"All handlers completed for event: {event}")

    def get_subscriber_count(self, event_type: type[Event]) -> int:
        """Get the number of subscribers for an event type"""
        return len(self._subscribers.get(event_type, []))


def get_event_bus(config_obj: Config) -> EventBus | EventBusInterface:
    if config_obj.event_bus == EventBusType.LOCAL:
        return EventBus()
    else:
        raise ValueError(f"Unsupported event bus type: {config_obj.event_bus}")


# singleton
event_bus = EventBus()
