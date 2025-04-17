import logging
from typing import cast

from src.now_the_game.telegram.memberships.memberships_model import (
    chat_membership_model,
)
from src.now_the_game.telegram.memberships.memberships_schemas import (
    AddChatMembershipPayload,
    ChangeChatMembershipPayload,
    ChatMembershipTable,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.event_registry import MembershipTopics
from src.shared.events import Event
from src.shared.observability.traces import async_traced_function
from src.shared.uow import current_uow

logger = logging.getLogger("deus-vult.telegram.memberships")


class MembershipsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = chat_membership_model

    @EventBus.subscribe(MembershipTopics.MEMBERSHIP_UPDATE)
    @async_traced_function
    async def on_change_chat_membership(self, event: Event) -> None:
        payload = cast(
            ChangeChatMembershipPayload,
            event.extract_payload(event, ChangeChatMembershipPayload),
        )

        chat_member_updated = payload.chat_member_updated
        logger.debug("New chat member: %s", chat_member_updated.chat.id)
        updated_info = payload.updated_info

        chat_id = chat_member_updated.chat.id
        user_id = updated_info.user.id

        chat_membership = ChatMembershipTable(
            user_id=user_id,
            chat_id=chat_id,
        )

        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            if payload.new_member:
                await self.model.add(db, chat_membership)
            else:
                await self.model.remove_secure(db, user_id, chat_id)
        else:
            logger.debug("No active uow, skipping")

    @EventBus.subscribe(MembershipTopics.MEMBERSHIP_CREATE)
    @async_traced_function
    async def on_add_chat_membership(self, event: Event) -> None:
        payload = cast(
            AddChatMembershipPayload,
            event.extract_payload(event, AddChatMembershipPayload),
        )
        logger.debug("Adding chat membership: %s", payload)

        chat_membership_core_info = await ChatMembershipTable.from_pyrogram(
            payload.message
        )

        active_uow = current_uow.get()

        if active_uow:
            db = await active_uow.get_session()
            if await self.model.not_exists(
                db,
                chat_membership_core_info.user_id,
                chat_membership_core_info.chat_id,
            ):
                await self.model.add(db, chat_membership_core_info)
            else:
                logger.debug(
                    "Chat membership %s %s already exists, skipping",
                    chat_membership_core_info.user_id,
                    chat_membership_core_info.chat_id,
                )
        else:
            logger.debug("No active uow, skipping")
