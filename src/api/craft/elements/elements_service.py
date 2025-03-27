from .... import Event, event_bus
from .elements_model import element_model
from .elements_schemas import (
    ElementCreatedEvent,
    ElementCreatedPayload,
    ElementGetEvent,
    ElementGetPayload,
    ElementGetResponse,
    ElementGetResponsePayload,
)


class ElementsService:
    def __init__(self):
        self.model = element_model
        self.event_bus = event_bus

        # Subscribe to events
        self.event_bus.subscribe_to_topic(
            ElementCreatedEvent.topic, self.on_add_element
        )
        self.event_bus.subscribe_to_topic(ElementGetEvent.topic, self.on_get_element)

    async def on_add_element(self, event: Event) -> None:
        if not isinstance(event.payload, ElementCreatedPayload):
            payload = ElementCreatedPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        raise NotImplementedError("Not implemented")

    async def on_get_element(self, event: Event) -> ElementGetResponse:
        if not isinstance(event.payload, ElementGetPayload):
            payload = ElementGetPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        element_id = payload.element_id if payload.element_id else None
        session = payload.db

        if element_id:
            element = await self.model.get(session, element_id=element_id)
        else:
            element = await self.model.get(session)

        response = ElementGetResponse(
            payload=ElementGetResponsePayload(elements=element)
        )
        return response
