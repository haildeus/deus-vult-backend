from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message, Poll

from .polls_model import poll_model, poll_options_model


class PollsService:
    def __init__(self, client: Client):
        self.client = client
        self.poll_model = poll_model
        self.poll_options_model = poll_options_model

    async def is_poll(self, message: Message) -> bool:
        return message.poll is not None

    async def get_poll(self, message: Message) -> Poll:
        if not self.is_poll(message):
            raise ValueError("Message is not a poll")
        return message.poll

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


polls_service = PollsService()
