from sqlalchemy.exc import SQLAlchemyError

from src.api import logger, logger_wrapper
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import (
    CreateElementPayload,
    ElementTable,
    ElementTopics,
    FetchElementPayload,
    FetchElementResponsePayload,
)
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model

    @EventBus.subscribe(ElementTopics.ELEMENT_CREATE.value)
    @logger_wrapper.log_debug
    async def on_create_element(self, event: Event) -> None:
        if not isinstance(event.payload, CreateElementPayload):
            payload = CreateElementPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        logger.debug(f"Creating element: {payload}")

        name = payload.name
        emoji = payload.emoji
        element = ElementTable(name=name, emoji=emoji)
        logger.debug(f"Creating element: {name} with emoji: {emoji}")

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                if await self.model.not_exists(db, name):
                    await self.model.add(db, element)
                else:
                    logger.debug(f"Element {name} already exists, skipping")
                    raise EntityAlreadyExistsError(
                        entity=name, entity_type=ElementTable.__name__
                    )
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error adding {name}: {e}")
                raise e
            except Exception as e:
                logger.error(f"Unexpected error adding {name}: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during element creation")

    @EventBus.subscribe(ElementTopics.ELEMENT_FETCH.value)
    @logger_wrapper.log_debug
    async def on_fetch_element(self, event: Event) -> FetchElementResponsePayload:
        if not isinstance(event.payload, FetchElementPayload):
            payload = FetchElementPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        element_id = payload.element_id
        name = payload.name
        logger.debug(f"Fetching element: {element_id} or {name}")

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                if element_id:
                    result = await self.model.get(db, element_id=element_id)
                elif name:
                    result = await self.model.get(db, name=name)
                else:
                    result = await self.model.get(db)

                logger.debug(f"Fetched elements: {result}")

                return FetchElementResponsePayload(elements=result)
            except SQLAlchemyError as e:
                logger.error(f"Error fetching {element_id} {name}: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error fetching {element_id} {name}: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during element fetching")
