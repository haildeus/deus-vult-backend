from typing import cast

from sqlalchemy.exc import SQLAlchemyError

from src.api import logger
from src.api.craft.elements.elements_constants import STARTING_ELEMENTS
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import Element, ElementTable, FetchElement
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics
from src.shared.events import Event
from src.shared.uow import current_uow


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model

    @EventBus.subscribe(ElementTopics.ELEMENTS_FETCH_INIT)
    async def on_fetch_init_elements(self, event: Event) -> list[ElementTable]:
        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            return await self.model.get_by_param_in_list(
                db, "name", [element.name for element in STARTING_ELEMENTS]
            )
        else:
            raise RuntimeError("No active UoW found during element initialization")

    @EventBus.subscribe(ElementTopics.ELEMENTS_INIT)
    async def on_init_elements(self, event: Event) -> None:
        starting_names = [element.name for element in STARTING_ELEMENTS]
        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            existing_elements: list[
                ElementTable
            ] = await self.model.get_by_param_in_list(db, "name", starting_names)
            if len(existing_elements) == len(STARTING_ELEMENTS):
                logger.debug("Starting elements already exist, skipping")
                return
            # Deduct the elements that do not exist
            missing_elements = [
                element
                for element in STARTING_ELEMENTS
                if element.name not in [e.name for e in existing_elements]
            ]
            for element in missing_elements:
                try:
                    element_entry = ElementTable(name=element.name, emoji=element.emoji)
                    await self.model.add(db, element_entry)
                except EntityAlreadyExistsError as e:
                    logger.debug(f"Element {element.name} already exists, skipping")
                    raise e
                except Exception as e:
                    logger.error(f"Unexpected error adding {element.name}: {e}")
                    raise e
        else:
            raise RuntimeError("No active UoW found during element initialization")

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
        logger.debug(f"Fetching elements. ID: {element_id}, Name(s): {name}")

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
