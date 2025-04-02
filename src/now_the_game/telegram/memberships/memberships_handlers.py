from collections.abc import Callable

from dependency_injector.wiring import Provide, inject
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.handlers.chat_member_updated_handler import ChatMemberUpdatedHandler
from pyrogram.handlers.handler import Handler
from pyrogram.types import ChatMemberUpdated

from src import Container
from src.now_the_game import logger
from src.shared.event_bus import EventBus
from src.shared.event_registry import ChatTopics, MembershipTopics, UserTopics
from src.shared.events import Event
from src.shared.uow import UnitOfWork


class ChatMembershipHandlers:
    """
    Chat membership handlers class
    """

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

        logger.debug(f"Processing chat membership: {chat_member_updated.chat.id}")
        new_member = True if chat_member_updated.new_chat_member else False
        logger.debug(f"Member is new: {new_member}")
        if new_member:
            updated_info = chat_member_updated.new_chat_member
        else:
            updated_info = chat_member_updated.old_chat_member

        actor_user = chat_member_updated.from_user
        target_user = updated_info.user

        uow = uow_factory()

        async with uow.start():
            shared_session = await uow.get_session()
            change_membership_event_payload = {
                "client": client,
                "chat_member_updated": chat_member_updated,
                "updated_info": updated_info,
                "db_session": shared_session,
                "new_member": new_member,
            }
            change_membership_event = Event(
                topic=MembershipTopics.MEMBERSHIP_UPDATE.value,
                payload=change_membership_event_payload,
            )

            add_actor_user_event_payload = {
                "client": client,
                "user": actor_user,
                "db_session": shared_session,
            }
            add_actor_user_event = Event(
                topic=UserTopics.USER_CREATE.value,
                payload=add_actor_user_event_payload,
            )

            add_target_user_event_payload = {
                "client": client,
                "user": target_user,
                "db_session": shared_session,
            }
            add_target_user_event = Event(
                topic=UserTopics.USER_CREATE.value,
                payload=add_target_user_event_payload,
            )

            add_chat_event_payload = {
                "client": client,
                "message": chat_member_updated,
                "db_session": shared_session,
            }
            add_chat_event = Event(
                topic=ChatTopics.CHAT_CREATE.value,
                payload=add_chat_event_payload,
            )

            # Publish the event and wait for all handlers to complete
            await event_bus.publish_and_wait(change_membership_event)
            await event_bus.publish_and_wait(add_actor_user_event)
            await event_bus.publish_and_wait(add_target_user_event)
            await event_bus.publish_and_wait(add_chat_event)

            logger.debug("All subscribers completed, flushing session")
            await shared_session.flush()

    @property
    def chat_membership_handlers(self) -> list[Handler]:
        return [
            ChatMemberUpdatedHandler(self.new_chat_membership, filters.group),
        ]
