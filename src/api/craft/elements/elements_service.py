from src import BaseService, Event, event_bus
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import (
    ElementCreatedPayload,
    ElementGetPayload,
    ElementGetResponse,
    ElementGetResponsePayload,
    ElementTopics,
)


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model

    @event_bus.subscribe(ElementTopics.ELEMENT_CREATED.value)
    async def on_add_element(self, event: Event) -> None:
        if not isinstance(event.payload, ElementCreatedPayload):
            payload = ElementCreatedPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        raise NotImplementedError("Not implemented")

    @event_bus.subscribe(ElementTopics.ELEMENT_GET.value)
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
