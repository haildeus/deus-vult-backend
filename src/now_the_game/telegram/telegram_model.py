from datetime import datetime

from pyrogram import Client
from pyrogram.types import (
    Animation,
    Chat,
    ChatMember,
    Message,
    Photo,
    Poll,
)


class TelegramModel:
    def __init__(self, client: Client):
        self.client = client

    """
    CHAT FUNCTIONS
    """

    async def get_chat(
        self,
        chat_id: int | str,
    ) -> Chat:
        chat_request = await self.client.get_chat(
            chat_id=chat_id,
        )
        return chat_request

    async def get_chat_member(
        self,
        chat_id: int | str,
        user_id: int | str,
    ) -> ChatMember:
        chat_member_request = await self.client.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )
        return chat_member_request

    async def get_chat_members_count(
        self,
        chat_id: int | str,
    ) -> int:
        chat_members_count_request = await self.client.get_chat_members_count(
            chat_id=chat_id,
        )
        return chat_members_count_request

    async def get_chat_photos(
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

    async def get_chat_photos_count(
        self,
        chat_id: int | str,
    ) -> int:
        chat_photos_count_request = await self.client.get_chat_photos_count(
            chat_id=chat_id,
        )
        return chat_photos_count_request

    """
    MESSAGE FUNCTIONS
    """

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

    """
    MEDIA FUNCTIONS
    """

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

    """
    POLL FUNCTIONS
    """

    async def send_poll(
        self,
        chat_id: int | str,
        question: str,
        options: list[str],
        schedule: datetime | None = None,
    ) -> Message:
        poll_message = await self.client.send_poll(
            chat_id=chat_id,
            question=question,
            options=options,
            schedule_date=schedule,
        )
        return poll_message

    async def stop_poll(
        self,
        chat_id: int | str,
        message_id: int,
    ) -> Poll:
        stopped_poll = await self.client.stop_poll(
            chat_id=chat_id,
            message_id=message_id,
        )
        return stopped_poll

    """
    MISC FUNCTIONS
    """
