from typing import cast

from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import (
    Element,
    ElementTable,
    ElementTopics,
    FetchElement,
)
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model
    
    @EventBus.subscribe(ElementTopics.ELEMENT_CREATE)
    async def on_create_element(self, event: Event) -> list[ElementTable]:
        payload = cast(Element, event.extract_payload(event, Element))
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
                    response = await self.model.add(db, element)
                    return response
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

    @EventBus.subscribe(ElementTopics.ELEMENT_FETCH)
    async def on_fetch_element(self, event: Event) -> list[ElementTable]:
        payload = cast(FetchElement, event.extract_payload(event, FetchElement))
        element_id = payload.element_id
        name = payload.name
        logger.debug(f"Fetching elements. "
                     f"ID: {element_id}, "
                     f"Name(s): {name}")

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            try:
                result = await self.model.get(db, element_id=element_id, name=name)
                logger.debug(f"Fetched elements: {result}")
                return result
            except SQLAlchemyError as e:
                logger.error(f"Error fetching {element_id} {name}: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error fetching {element_id} {name}: {e}")
                raise e
        else:
            raise RuntimeError("No active UoW found during element fetching")
