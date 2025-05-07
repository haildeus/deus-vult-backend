import logging
from typing import cast

from src.api.craft.elements.elements_constants import STARTING_ELEMENTS
from src.api.inventory.inventory_schemas import InventoryItemTable, InventoryTable
from src.api.users.users_schemas import NewUserPayload
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import UserTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.api.craft")


class InventoryService(BaseService):
    @EventBus.subscribe(UserTopics.USER_INIT)
    @async_traced_function
    async def on_user_init(self, event: Event) -> None:
        payload = cast(
            NewUserPayload,
            event.extract_payload(event, NewUserPayload),
        )

        user = payload.user
        uow = current_uow.get()
        session = await uow.get_session()

        new_inventory = InventoryTable(
            user_id=user.object_id,
            items=[
                InventoryItemTable(
                    type=InventoryItemTable.ItemType.ELEMENT,
                    sub_type_id=element.object_id,
                    amount=100,
                )
                for element in STARTING_ELEMENTS
            ],
        )

        session.add(new_inventory)
        await session.flush()
        await session.refresh(new_inventory)
