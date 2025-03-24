from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from .. import logger
from .chats import ChatBase, chat_model
from .membership import ChatMembershipBase, chat_membership_model
from .messages import MessageBase, message_model
from .polls import PollBase, PollOptionsBase, poll_model, poll_option_model
from .telegram_exceptions import PyrogramConversionError
from .users import UserBase, user_model


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
        logger.debug("Telegram Orchestrator initialized")

    async def process_new_message(
        self, session: AsyncSession, message: Message
    ) -> bool:
        """Process a new incoming message"""
        try:
            message_base = await MessageBase.from_pyrogram(message)
            chat_base = await ChatBase.from_pyrogram(message)
            user_base = await UserBase.from_pyrogram(message)
        except PyrogramConversionError as e:
            logger.error(f"Error converting message to MessageCore: {e}")
            raise e

        user_added = await self.check_or_add_user_and_chat(
            session, user_base, chat_base
        )
        message_added = await self.check_or_add_message(session, message_base)

        if await self.poll.is_poll(message):
            poll_base = await PollBase.from_pyrogram(message)
            await self.poll.add(session, poll_base)
            poll_options_array: list[PollOptionsBase] = []

            for option_position in range(len(message.poll.options)):
                poll_option_base = await PollOptionsBase.from_pyrogram(
                    poll_base.object_id, option_position, message
                )
                poll_options_array.append(poll_option_base)

            for poll_option_base in poll_options_array:
                await self.poll_option.add(session, poll_option_base)

        return user_added and message_added

    async def check_or_add_user_and_chat(
        self, session: AsyncSession, user: UserBase, chat: ChatBase
    ) -> bool:
        """Add a new user and chat to the database"""
        try:
            assert user
            assert chat
        except AssertionError as e:
            logger.error(f"Error adding new user to the database: {e}")
            raise e

        # Check if user exists
        db_user = await self.user.get(session, user_id=user.object_id)
        if not db_user:
            await self.user.add(session, user)

        # Check if chat exists
        db_chat = await self.chat.get(session, chat_id=chat.object_id)
        if not db_chat:
            await self.chat.add(session, chat)

        if not db_user or not db_chat:
            chat_membership = ChatMembershipBase(
                user_id=user.object_id,
                chat_id=chat.object_id,
            )
            await self.chat_membership.add(session, chat_membership)

        return True

    async def check_or_add_message(
        self, session: AsyncSession, message: MessageBase
    ) -> bool:
        try:
            assert message
        except AssertionError as e:
            logger.error(f"Error adding new message to the database: {e}")
            raise e

        db_message = await self.message.get(session, chat_id=message.chat_id)
        if not db_message:
            await self.message.add(session, message)
            return True
        return False
