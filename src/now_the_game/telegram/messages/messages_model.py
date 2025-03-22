from typing import overload, cast

from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.base import BaseModel
from ..telegram_model import telegram_model
from ..telegram_schemas import MessageBase
from ... import logger


class MessageModel(BaseModel[MessageBase]):
    def __init__(self):
        super().__init__(MessageBase)
        self._telegram_model = telegram_model  # Reuse existing singleton

    async def add_message(
        self,
        session: AsyncSession,
        message: Message,
    ) -> bool:
        """
        Add a message from Pyrogram to the database.
        Leverages the existing TelegramModel for efficiency.

        Args:
            session: SQLAlchemy async session
            message: Pyrogram message object

        Returns:
            True if the message was added successfully, False otherwise
        """
        try:
            # Add all entities for this message
            await self._telegram_model.add_from_pyrogram(session, message)

            # Always flush to ensure the entities are created
            await session.flush()

            # Otherwise, fetch the message entity specifically
            return True
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False

    async def bulk_add_messages(
        self, session: AsyncSession, messages: list[Message]
    ) -> list[MessageBase]:
        """
        Add multiple messages from Pyrogram in bulk.

        Args:
            session: SQLAlchemy async session
            messages: List of Pyrogram message objects
            optimized: Whether to use the optimized batch processing (default: True)

        Returns:
            List of created MessageBase objects
        """
        if not messages:
            return []

        # Optimized batch processing using transaction
        processed_msgs: list[MessageBase] = []

        # Use transaction to ensure atomicity
        try:
            # Process each message using the telegram_model directly
            # This avoids redundant entity creation by handling deduplication
            for message in messages:
                try:
                    # First add all entities for this message
                    await self._telegram_model.add_from_pyrogram(session, message)

                    # Then get just the message entity
                    msg = cast(
                        MessageBase,
                        await self._telegram_model.add_from_pyrogram(
                            session, message, "message"
                        ),
                    )
                    processed_msgs.append(msg)
                except Exception as e:
                    logger.error(f"Error processing message in batch: {e}")
                    continue

            # Flush once to commit all entities
            await session.flush()
            return processed_msgs

        except Exception as e:
            logger.error(f"Error in bulk message processing: {e}")
            raise e


message_model = MessageModel()
