from src import BaseService, EntityAlreadyExistsError, Event, event_bus
from src.api import logger, logger_wrapper
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import (
    CreateElementPayload,
    ElementTable,
    ElementTopics,
    FetchElementPayload,
    FetchElementResponsePayload,
)


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model

    @event_bus.subscribe(ElementTopics.ELEMENT_CREATE.value)
    @logger_wrapper.log_debug
    async def on_create_element(self, event: Event) -> None:
        if not isinstance(event.payload, CreateElementPayload):
            payload = CreateElementPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Creating element: {payload}")

        name = payload.name
        emoji = payload.emoji
        db = payload.db_session

        logger.debug(f"Creating element: {name} with emoji: {emoji}")

        element = ElementTable(name=name, emoji=emoji)
        if await self.model.not_exists(db, name):
            logger.debug(f"Element {name} does not exist, adding to database")
            await self.model.add(db, element)
        else:
            logger.debug(f"Element {name} already exists, skipping")
            raise EntityAlreadyExistsError(
                entity=name, entity_type=ElementTable.__name__
            )

    @event_bus.subscribe(ElementTopics.ELEMENT_FETCH.value)
    @logger_wrapper.log_debug
    async def on_fetch_element(self, event: Event) -> FetchElementResponsePayload:
        if not isinstance(event.payload, FetchElementPayload):
            payload = FetchElementPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        element_id = payload.element_id
        name = payload.name
        db = payload.db_session

        logger.debug(f"Fetching element: {element_id} or {name}")

        if element_id:
            result = await self.model.get(db, element_id=element_id)
        elif name:
            result = await self.model.get(db, name=name)
        else:
            result = await self.model.get(db)

        logger.debug(f"Fetched elements: {result}")

        return FetchElementResponsePayload(elements=result)


elements_service = ElementsService()
