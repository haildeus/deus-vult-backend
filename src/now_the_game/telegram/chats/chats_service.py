from pyrogram import Client
from pyrogram.types import Animation, Chat, ChatMember, Photo

from .chats_model import chat_model


class ChatsService:
    def __init__(self, client: Client):
        self.client = client
        self.chat_model = chat_model

    async def get(
        self,
        chat_id: int | str,
    ) -> Chat:
        chat_request = await self.client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

    async def get_member(
        self,
        chat_id: int | str,
        user_id: int | str,
    ) -> ChatMember:
        chat_member_request = await self.client.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
        return chat_member_request

    async def get_members_count(
        self,
        chat_id: int | str,
    ) -> int:
        chat_members_count_request = await self.client.get_chat_members_count(
            chat_id=chat_id,
        )
        return chat_members_count_request

    async def get_photos(
        self,
        chat_id: int | str,
    ) -> list[Photo] | list[Animation]:
        """
        Returns a generator Photo | Animation
        """
        chat_photos_request = await self.client.get_chat_photos(
            chat_id=chat_id,
        )
        return chat_photos_request

    async def get_photos_count(
        self,
        chat_id: int | str,
    ) -> int:
        chat_photos_count_request = await self.client.get_chat_photos_count(
            chat_id=chat_id,
        )
        return chat_photos_count_request
