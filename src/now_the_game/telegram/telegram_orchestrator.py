from pyrogram.client import Client
from pyrogram.types import ChatMemberUpdated, Message

from .. import db, logger
from .chats.chats_model import chat_model
from .chats.chats_schemas import ChatTable
from .client import telegram
from .memberships.memberships_model import chat_membership_model
from .memberships.memberships_schemas import ChatMembershipTable
from .messages.messages_model import message_model
from .messages.messages_schemas import MessageTable
from .polls.polls_model import (
    poll_model,
    poll_option_model,
)
from .polls.polls_schemas import PollOptionTable, PollTable
from .users.users_model import user_model
from .users.users_schemas import UserTable


class TelegramOrchestrator:
    """
    Orchestrator for Telegram events
    """

    def __init__(self):
        logger.debug("Initializing Telegram Orchestrator")
        self.chat = chat_model
        self.chat_membership = chat_membership_model
        self.message = message_model
        self.poll = poll_model
        self.poll_option = poll_option_model
        self.user = user_model
        self.telegram = telegram
        logger.debug("Telegram Orchestrator initialized")

    async def new_chat_member(
        self,
        client: Client,
        chat_member_updated: ChatMemberUpdated,
        new_member: bool,
    ):
        """
        Process a new chat member event and add it to the database
        """
        logger.debug(f"New chat member: {chat_member_updated.chat.id}")
        if new_member:
            updated_info = chat_member_updated.new_chat_member
        else:
            updated_info = chat_member_updated.old_chat_member

        actor_user = chat_member_updated.from_user
        target_user = updated_info.user

        # We need to update: chat, user, chat_membership
        chat_core_info = await ChatTable.from_pyrogram(chat_member_updated)
        user_actor_core_info = await UserTable.from_user(actor_user)
        user_target_core_info = await UserTable.from_user(target_user)
        chat_membership_core_info = await ChatMembershipTable.create(
            user_id=user_target_core_info.object_id,
            chat_id=chat_core_info.object_id,
        )

        async with db.session() as session:
            await self.chat.add(session, chat_core_info)
            await self.user.add(session, user_actor_core_info)
            await self.user.add(session, user_target_core_info)
            if new_member:
                await self.chat_membership.add(session, chat_membership_core_info)
            else:
                await self.chat_membership.remove_secure(
                    session,
                    user_id=user_target_core_info.object_id,
                    chat_id=chat_core_info.object_id,
                )
            await session.flush()
            logger.debug("Flushed session")

        logger.debug(f"Processed new chat member update for {chat_core_info.object_id}")

    async def send_poll(
        self,
        client: Client,
        chat_id: int | str,
        question: str,
        options: list[str],
        is_anonymous: bool = True,
        explanation: str | None = None,
        save_to_db: bool = True,
    ):
        poll_message = await self.telegram.send_poll(
            client=client,
            chat_id=chat_id,
            question=question,
            options=options,
            is_anonymous=is_anonymous,
            explanation=explanation,
        )

        if save_to_db:
            poll_from_pyrogram = await PollTable.from_pyrogram(poll_message)
            poll_options_from_pyrogram = await PollOptionTable.from_pyrogram(
                poll_id=poll_from_pyrogram.object_id, options=poll_message.poll.options
            )

            async with db.session() as session:
                await self.poll.add(session, poll_from_pyrogram)
                await self.poll_option.add(session, poll_options_from_pyrogram)
                await session.flush()

    async def new_message(self, message: Message):
        """
        Process a message from Telegram and add it to the database
        """
        message_core_info = await MessageTable.from_pyrogram(message)
        chat_core_info = await ChatTable.from_pyrogram(message)
        user_core_info = await UserTable.from_pyrogram(message)
        chat_membership_core_info = await ChatMembershipTable.from_pyrogram(message)

        async with db.session() as session:
            await self.message.add(session, message_core_info)
            await self.chat.add(session, chat_core_info)
            await self.user.add(session, user_core_info)

            chat_id = chat_membership_core_info.chat_id
            user_id = chat_membership_core_info.user_id
            if await self.chat_membership.not_exists(session, user_id, chat_id):
                await self.chat_membership.add(session, chat_membership_core_info)

            await session.flush()


telegram_orchestrator = TelegramOrchestrator()
