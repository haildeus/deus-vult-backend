import logging
from typing import cast

from sqlmodel import select

from src.api.users.users_schemas import (
    AddUserPayload,
    NewUserPayload,
    UserTable,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import UserTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.telegram.users")


class UsersService(BaseService):
    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus

    @async_traced_function
    async def create_or_update(
        self,
        user: UserTable,
    ) -> UserTable:
        uow = current_uow.get()
        session = await uow.get_session()

        stmt = select(
            select(UserTable).where(UserTable.object_id == user.object_id).exists()
        )
        exits = (await session.execute(stmt)).scalar()
        if exits:
            logger.debug("Updating existing user")
            return await session.merge(user)
        else:
            logger.debug("Creating new user")
            session.add(user)
            # noinspection PyTypeChecker
            await self.event_bus.publish_and_wait(
                Event(
                    topic=UserTopics.USER_INIT.value,
                    payload=NewUserPayload(
                        user=user,
                    ),
                )
            )
            await session.commit()
            await session.refresh(user)
            return user

    @EventBus.subscribe(UserTopics.USER_CREATE_FROM_TELEGRAM)
    @async_traced_function
    async def on_add_user_from_telegram(self, event: Event) -> None:
        payload = cast(
            AddUserPayload,
            event.extract_payload(event, AddUserPayload),
        )

        user = payload.user
        user_core_info = await UserTable.from_user(user)
        await self.create_or_update(user=user_core_info)
