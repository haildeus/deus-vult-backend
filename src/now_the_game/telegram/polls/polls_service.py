from datetime import datetime

from pyrogram.client import Client
from pyrogram.types import Message, Poll

from src import BaseService, Event, event_bus
from src.now_the_game import db, logger
from src.now_the_game.telegram.polls.polls_model import poll_model, poll_option_model
from src.now_the_game.telegram.polls.polls_schemas import (
    PollOptionTable,
    PollTable,
    PollTopics,
    SendPollEventPayload,
)


class PollsService(BaseService):
    def __init__(self, client: Client):
        super().__init__()
        self.client = client
        self.poll_model = poll_model
        self.poll_option_model = poll_option_model
        self.db = db
        self.event_bus = event_bus

    @event_bus.subscribe(PollTopics.POLL_SEND.value)
    async def on_send_poll(self, event: Event) -> None:
        logger.debug(f"Received send poll event: {event}")
        if not isinstance(event.payload, SendPollEventPayload):
            payload = SendPollEventPayload(**event.payload)  # type: ignore
        else:
            payload = event.payload

        save_to_db = payload.save

        logger.debug(f"Sending poll to {payload.chat_id}")
        poll_message = await self.client.send_poll(
            chat_id=payload.chat_id,
            question=payload.question,
            options=payload.options,
            is_anonymous=payload.is_anonymous,
            explanation=payload.explanation,
        )
        logger.debug(f"Poll sent to {payload.chat_id}")

        if save_to_db:
            logger.debug("Converting poll to database model")
            poll_from_pyrogram = await PollTable.from_pyrogram(poll_message)
            poll_options_from_pyrogram = await PollOptionTable.from_pyrogram(
                poll_id=poll_from_pyrogram.object_id, options=poll_message.poll.options
            )

            logger.debug("Adding poll to database")
            async with self.db.session() as session:
                await self.poll_model.add(session, poll_from_pyrogram)
                await self.poll_option_model.add(session, poll_options_from_pyrogram)
                await session.flush()

    async def is_poll(self, message: Message) -> bool:
        try:
            assert message.poll
            return True
        except AssertionError:
            return False

    async def get_poll(self, message: Message) -> Poll:
        if not await self.is_poll(message):
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
