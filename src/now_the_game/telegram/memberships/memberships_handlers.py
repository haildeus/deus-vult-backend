import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from dependency_injector.wiring import Provide, inject
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.chat_member_updated_handler import ChatMemberUpdatedHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import ChatMemberUpdated

from src import Container
from src.shared.event_bus import EventBus
from src.shared.event_registry import ChatTopics, MembershipTopics, UserTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import UnitOfWork

logger = logging.getLogger("deus-vult.telegram.memberships")


class ChatMembershipHandlers:
    """
    Chat membership handlers class
    """

    @async_traced_function
    @inject
    async def new_chat_membership(
        self,
        client: Client,
        chat_member_updated: ChatMemberUpdated,
        uow_factory: Callable[[], UnitOfWork] = Provide[Container.uow_factory],
        event_bus: EventBus = Provide[Container.event_bus],
    ) -> None:
        """
        Process a new chat membership event and add it to the database.
        """

        logger.debug("Processing chat membership: %s", chat_member_updated.chat.id)
        new_member = True if chat_member_updated.new_chat_member else False
        logger.debug("Member is new: %s", new_member)
        if new_member:
            updated_info = chat_member_updated.new_chat_member
        else:
            updated_info = chat_member_updated.old_chat_member

        actor_user = chat_member_updated.from_user
        target_user = updated_info.user

        uow = uow_factory()

        async with uow.start():
            shared_session = await uow.get_session()

            change_membership_event = Event.from_dict(
                MembershipTopics.MEMBERSHIP_UPDATE.value,
                {
                    "chat_member_updated": chat_member_updated,
                    "updated_info": updated_info,
                    "new_member": new_member,
                },
            )

            add_actor_user_event = Event.from_dict(
                UserTopics.USER_CREATE.value,
                {"user": actor_user},
            )

            add_target_user_event = Event.from_dict(
                UserTopics.USER_CREATE.value,
                {"user": target_user},
            )

            add_chat_event = Event.from_dict(
                ChatTopics.CHAT_CREATE.value,
                {"message": chat_member_updated},
            )

            # Publish the event and wait for all handlers to complete
            async_tasks: list[Coroutine[Any, Any, None]] = [
                event_bus.publish_and_wait(change_membership_event),
                event_bus.publish_and_wait(add_actor_user_event),
                event_bus.publish_and_wait(add_target_user_event),
                event_bus.publish_and_wait(add_chat_event),
            ]
            await asyncio.gather(*async_tasks)

            logger.debug("All subscribers completed, flushing session")
            await shared_session.flush()

    @property
    def chat_membership_handlers(self) -> list[Handler]:
        return [
            ChatMemberUpdatedHandler(self.new_chat_membership, filters.group),
        ]
