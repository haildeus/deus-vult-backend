from pyrogram.client import Client
from pyrogram.types import Chat, ChatMember
from sqlalchemy.exc import SQLAlchemyError

from src.now_the_game import logger, logger_wrapper
from src.now_the_game.telegram.chats.chats_model import chat_model
from src.now_the_game.telegram.chats.chats_schemas import (
    AddChatEventPayload,
    ChatTable,
    ChatTopics,
)
from src.shared.base import BaseService
from src.shared.event_bus import EventBus
from src.shared.events import Event
from src.shared.uow import current_uow


class ChatsService(BaseService):
    def __init__(self):
        super().__init__()
        self.model = chat_model

    @EventBus.subscribe(ChatTopics.CHAT_CREATE.value)
    @logger_wrapper.log_debug
    async def on_add_chat(self, event: Event) -> None:
        if not isinstance(event.payload, AddChatEventPayload):
            payload = AddChatEventPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        chat_core_info = await ChatTable.from_pyrogram(payload.message)
        logger.debug(f"Adding chat: {chat_core_info}")

        active_uow = current_uow.get()
        if active_uow:
            db = await active_uow.get_session()
            try:
                await self.model.add(db, chat_core_info)
            except SQLAlchemyError as e:
                logger.error(f"SQLAlchemy error adding {chat_core_info.object_id}: {e}")
                raise e
            except Exception as e:
                logger.error(f"Error adding chat {chat_core_info.object_id}: {e}")
                raise e
        else:
            logger.debug("No active uow, skipping")

    async def get(self, chat_id: int | str, client: Client) -> Chat:
        chat_request = await client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

    async def download_chat_photo(
        self,
        chat_id: int | str,
        client: Client,
    ) -> bytes:
        chat = await self.get(chat_id, client)
        photo_small = chat.photo.small_file_id
        bytes_io_object = await client.download_media(  # type: ignore
            message=photo_small,
            in_memory=True,
        )
        bytes_object = bytes_io_object.getvalue()  # type: ignore
        if bytes_object is None:
            raise ValueError("Bytes object is None")

        return bytes_object  # type: ignore

    async def get_member(
        self,
        chat_id: int | str,
        user_id: int | str,
        client: Client,
    ) -> ChatMember:
        chat_member_request = await client.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
        return chat_member_request

    async def get_members_count(
        self,
        chat_id: int | str,
        client: Client,
    ) -> int:
        chat_members_count_request = await client.get_chat_members_count(
            chat_id=chat_id,
        )
        return chat_members_count_request

    async def get_photos_count(
        self,
        chat_id: int | str,
        client: Client,
    ) -> int:
        chat_photos_count_request = await client.get_chat_photos_count(
            chat_id=chat_id,
        )
        return chat_photos_count_request
