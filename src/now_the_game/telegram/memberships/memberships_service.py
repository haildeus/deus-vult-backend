from src.now_the_game import logger, logger_wrapper
from src.now_the_game.telegram.memberships.memberships_model import (
    chat_membership_model,
)
from src.now_the_game.telegram.memberships.memberships_schemas import (
    AddChatMembershipPayload,
    ChangeChatMembershipPayload,
    ChatMembershipTable,
    MembershipTopics,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class MembershipsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = chat_membership_model

    @EventBus.subscribe(MembershipTopics.MEMBERSHIP_UPDATE.value)
    @logger_wrapper.log_debug
    async def on_change_chat_membership(self, event: Event) -> None:
        if not isinstance(event.payload, ChangeChatMembershipPayload):
            payload = ChangeChatMembershipPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        chat_member_updated = payload.chat_member_updated

        logger.debug(f"New chat member: {chat_member_updated.chat.id}")
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

    @EventBus.subscribe(MembershipTopics.MEMBERSHIP_CREATE.value)
    async def on_add_chat_membership(self, event: Event) -> None:
        if not isinstance(event.payload, AddChatMembershipPayload):
            payload = AddChatMembershipPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

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
                    f"Chat membership {chat_membership_core_info.user_id} {chat_membership_core_info.chat_id} already exists, skipping"
                )
        else:
            logger.debug("No active uow, skipping")
