from src import BaseService, Event, event_bus
from src.now_the_game import logger
from src.now_the_game.telegram.memberships.memberships_model import (
    chat_membership_model,
)
from src.now_the_game.telegram.memberships.memberships_schemas import (
    AddChatMembershipPayload,
    ChangeChatMembershipPayload,
    ChatMembershipTable,
    MembershipTopics,
)


class MembershipsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = chat_membership_model

    @event_bus.subscribe(MembershipTopics.MEMBERSHIP_UPDATE.value)
    async def on_change_chat_membership(self, event: Event) -> None:
        if not isinstance(event.payload, ChangeChatMembershipPayload):
            payload = ChangeChatMembershipPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        chat_member_updated = payload.chat_member_updated
        db = payload.db_session

        logger.debug(f"New chat member: {chat_member_updated.chat.id}")
        updated_info = payload.updated_info

        chat_id = chat_member_updated.chat.id
        user_id = updated_info.user.id

        chat_membership = ChatMembershipTable(
            user_id=user_id,
            chat_id=chat_id,
        )

        if payload.new_member:
            await self.model.add(db, chat_membership)
        else:
            await self.model.remove_secure(db, user_id, chat_id)

    @event_bus.subscribe(MembershipTopics.MEMBERSHIP_CREATE.value)
    async def on_add_chat_membership(self, event: Event) -> None:
        if not isinstance(event.payload, AddChatMembershipPayload):
            payload = AddChatMembershipPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        chat_membership_core_info = await ChatMembershipTable.from_pyrogram(
            payload.message
        )

        if await self.model.not_exists(
            payload.db_session,
            chat_membership_core_info.user_id,
            chat_membership_core_info.chat_id,
        ):
            await self.model.add(payload.db_session, chat_membership_core_info)
