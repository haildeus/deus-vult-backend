import logging
from typing import cast

from opentelemetry.trace import get_current_span
from sqlalchemy.exc import SQLAlchemyError

from src.api.craft.elements.elements_constants import STARTING_ELEMENTS
from src.api.craft.elements.elements_model import element_model
from src.api.craft.elements.elements_schemas import Element, ElementTable, FetchElement
from src.shared.base import BaseService, EntityAlreadyExistsError
from src.shared.event_bus import EventBus
from src.shared.event_registry import ElementTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.api.craft")


class ElementsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = element_model

    @EventBus.subscribe(ElementTopics.ELEMENTS_FETCH_INIT)
    @async_traced_function
    async def on_fetch_init_elements(self, event: Event) -> list[ElementTable]:
        _ = event

        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            return await self.model.get_by_param_in_list(
                db, "name", [element.name for element in STARTING_ELEMENTS]
            )
        else:
            raise RuntimeError("No active UoW found during element initialization")

    @EventBus.subscribe(ElementTopics.ELEMENTS_INIT)
    @async_traced_function
    async def on_init_elements(self, event: Event) -> None:
        _ = event

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
                    logger.debug("Element %s already exists, skipping", element.name)
                    raise e
                except Exception as e:
                    logger.error("Unexpected error adding %s: %s", element.name, e)
                    raise e
        else:
            raise RuntimeError("No active UoW found during element initialization")

    @EventBus.subscribe(ElementTopics.ELEMENT_CREATE)
    @async_traced_function
    async def on_create_element(self, event: Event) -> list[ElementTable]:
        payload = cast(Element, event.extract_payload(event, Element))
        logger.debug("Creating element: %s", payload)

        name = payload.name
        emoji = payload.emoji
        element = ElementTable(name=name, emoji=emoji)

        span = get_current_span()
        span.set_attribute("name", name)
        span.set_attribute("emoji", emoji)
        logger.debug("Creating element: %s with emoji: %s", name, emoji)

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()

            try:
                if await self.model.not_exists(db, name):
                    response = await self.model.add(db, element)
                    return response
                else:
                    logger.warning("Element %s already exists, skipping", name)
                    raise EntityAlreadyExistsError(
                        entity=name, entity_type=ElementTable.__name__
                    )
            except EntityAlreadyExistsError:
                logger.warning("Element %s already exists, returning element", name)
                return [element]
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy error adding %s: %s", name, e)
                raise e
            except Exception as e:
                logger.error("Unexpected error adding %s: %s", name, e)
                raise e
        else:
            raise RuntimeError("No active UoW found during element creation")

    @EventBus.subscribe(ElementTopics.ELEMENT_FETCH)
    @async_traced_function
    async def on_fetch_element(self, event: Event) -> list[ElementTable]:
        payload = cast(FetchElement, event.extract_payload(event, FetchElement))
        element_id = payload.element_id
        name = payload.name

        span = get_current_span()
        span.set_attribute("element_id", element_id)
        span.set_attribute("name", name)
        logger.debug("Fetching elements. ID: %s, Name(s): %s", element_id, name)

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            try:
                result = await self.model.get(db, element_id=element_id, name=name)
                logger.debug("Fetched elements: %s", result)
                return result
            except SQLAlchemyError as e:
                logger.error("Error fetching %s %s: %s", element_id, name, e)
                raise e
            except Exception as e:
                logger.error("Error fetching %s %s: %s", element_id, name, e)
                raise e
        else:
            raise RuntimeError("No active UoW found during element fetching")
