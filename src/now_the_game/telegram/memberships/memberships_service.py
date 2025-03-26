from ... import event_bus, logger
from ...core.events import Event
from .memberships_model import chat_membership_model
from .memberships_schemas import (
    AddChatMembershipEvent,
    AddChatMembershipPayload,
    ChangeChatMembershipEvent,
    ChangeChatMembershipPayload,
    ChatMembershipTable,
)


class MembershipsService:
    def __init__(self):
        self.event_bus = event_bus
        self.model = chat_membership_model

        # subscribe to events
        self.event_bus.subscribe_to_topic(
            ChangeChatMembershipEvent.topic, self.on_change_chat_membership
        )
        self.event_bus.subscribe_to_topic(
            AddChatMembershipEvent.topic, self.on_add_chat_membership
        )

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
