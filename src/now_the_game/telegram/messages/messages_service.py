from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message

from .messages_model import message_model


class MessagesService:
    def __init__(self, client: Client):
        self.client = client
        self.message_model = message_model

    async def get_messages(
        self,
        chat_id: int | str,
        message_ids: list[int] | int,
    ) -> list[Message] | Message:
        message_request = await self.client.get_messages(
            chat_id=chat_id,
            message_ids=message_ids,
        )
        return message_request

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        schedule: datetime | None = None,
    ) -> Message:
        message = await self.client.send_message(
            chat_id=chat_id,
            text=text,
            schedule_date=schedule,
        )
        return message

    async def send_photo(
        self,
        chat_id: int | str,
        photo: str,
        caption: str | None = None,
        schedule: datetime | None = None,
        ttl_seconds: int | None = None,
    ) -> Message:
        photo_message = await self.client.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            schedule_date=schedule,
            ttl_seconds=ttl_seconds,
        )
        return photo_message

    async def send_game(
        self,
        chat_id: int | str,
        game_short_name: str,
    ) -> Message:
        game_message = await self.client.send_game(
            chat_id=chat_id,
            game_short_name=game_short_name,
        )
        return game_message

    async def set_game_score(
        self,
        chat_id: int | str,
        message_id: int,
        user_id: int | str,
        score: int,
        force: bool = False,
    ) -> Message:
        set_game_score_message = await self.client.set_game_score(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            score=score,
            force=force,
        )
        return set_game_score_message
