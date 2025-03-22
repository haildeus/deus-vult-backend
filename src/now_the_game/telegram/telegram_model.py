from typing import Literal, TypeVar, overload

from pyrogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from .. import logger
from ..core.base import BaseModel, BaseSchema, EntityAlreadyExistsError
from .telegram_exceptions import PyrogramConversionError
from .telegram_schemas import (
    ChatBase,
    ChatMembershipBase,
    MessageBase,
    MessageCore,
    UserBase,
    UserChatLinkBase,
)

T = TypeVar("T", bound=BaseSchema)
EntityType = Literal["message", "chat", "user", "user_chat_link", "chat_membership"]


class TelegramModel(BaseModel[MessageBase]):
    def __init__(self):
        super().__init__(MessageBase)

    @overload
    async def _add_entity(
        self, session: AsyncSession, entity_type: type[MessageBase], entity: MessageBase
    ) -> None: ...

    @overload
    async def _add_entity(
        self, session: AsyncSession, entity_type: type[ChatBase], entity: ChatBase
    ) -> None: ...

    @overload
    async def _add_entity(
        self, session: AsyncSession, entity_type: type[UserBase], entity: UserBase
    ) -> None: ...

    @overload
    async def _add_entity(
        self,
        session: AsyncSession,
        entity_type: type[ChatMembershipBase],
        entity: ChatMembershipBase,
    ) -> None: ...

    async def _add_entity(
        self, session: AsyncSession, entity_type: type[T], entity: T
    ) -> None:
        """Add an entity to the database that inherits from BaseSchema"""
        try:
            model = BaseModel[T](entity_type)
            await model.add(session, entity)
        except PyrogramConversionError as e:
            logger.error(
                f"Error adding {entity_type.__name__} from pyrogram message: {e}"
            )
            raise e
        except EntityAlreadyExistsError as e:
            logger.error(f"Entity {entity_type.__name__} already exists: {e}")
            raise e
        except Exception as e:
            logger.error(
                f"Error adding {entity_type.__name__} from pyrogram message: {e}"
            )
            raise e

    async def _add_user_chat_link(
        self, session: AsyncSession, entity: UserChatLinkBase
    ) -> None:
        """Add a user chat link entity (which doesn't inherit from BaseSchema)"""
        try:
            session.add(entity)
            await session.flush()
        except Exception as e:
            logger.error(f"Error adding UserChatLinkBase from pyrogram message: {e}")
            raise e

    @overload
    async def add_from_pyrogram(
        self, session: AsyncSession, message: Message
    ) -> None: ...

    @overload
    async def add_from_pyrogram(
        self, session: AsyncSession, message: Message, entity_type: EntityType
    ) -> MessageBase | ChatBase | UserBase | UserChatLinkBase | ChatMembershipBase: ...

    async def add_from_pyrogram(
        self,
        session: AsyncSession,
        message: Message,
        entity_type: EntityType | None = None,
    ) -> (
        MessageBase | ChatBase | UserBase | UserChatLinkBase | ChatMembershipBase | None
    ):
        """Add entities from a pyrogram message.

        Args:
            session: The database session
            message: The pyrogram message
            entity_type: Optional - specify a single entity type to process
                        ('message', 'chat', 'user', 'user_chat_link', 'chat_membership')

        Returns:
            The processed entity if entity_type is specified, otherwise None
        """
        try:
            msg_core = await MessageCore.from_pyrogram(message)

            # Process based on entity_type if specified
            if entity_type == "message":
                await self._add_entity(session, MessageBase, msg_core.message)
                return msg_core.message
            elif entity_type == "chat":
                await self._add_entity(session, ChatBase, msg_core.chat)
                return msg_core.chat
            elif entity_type == "user":
                await self._add_entity(session, UserBase, msg_core.user)
                return msg_core.user
            elif entity_type == "user_chat_link":
                await self._add_user_chat_link(session, msg_core.user_chat_link)
                return msg_core.user_chat_link
            elif entity_type == "chat_membership":
                await self._add_entity(
                    session, ChatMembershipBase, msg_core.chat_membership
                )
                return msg_core.chat_membership

            # If no entity_type specified, process all entities
            elif entity_type is None:
                await self._add_entity(session, MessageBase, msg_core.message)
                await self._add_entity(session, ChatBase, msg_core.chat)
                await self._add_entity(session, UserBase, msg_core.user)
                await self._add_user_chat_link(session, msg_core.user_chat_link)
                await self._add_entity(
                    session, ChatMembershipBase, msg_core.chat_membership
                )
                return None

        except PyrogramConversionError as e:
            logger.error(f"Error processing pyrogram message: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error processing pyrogram message: {e}")
            raise e

        return None


telegram_model = TelegramModel()
