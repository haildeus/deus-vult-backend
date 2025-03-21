from pyrogram import Client
from pyrogram.types import Animation, Chat, Photo

from .users_model import user_model


class UsersService:
    def __init__(self, client: Client):
        self.client = client
        self.user_model = user_model

    async def get(
        self,
        chat_id: int | str,
    ) -> Chat:
        chat_request = await self.client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

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
