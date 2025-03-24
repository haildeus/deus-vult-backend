from datetime import datetime
from enum import Enum

from pyrogram.types import Message
from sqlmodel import Field

from ...core.base import BaseSchema
from ..telegram_exceptions import PyrogramConversionError


class PollType(Enum):
    QUIZ = "quiz"
    POLL = "poll"


class PollBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.object_id")
    message_id: int = Field(foreign_key="messages.object_id")
    question: str = Field(min_length=1, max_length=300)
    poll_type: PollType = Field(default=PollType.POLL)
    is_anonymous: bool = Field(default=True)
    close_date: datetime | None = Field(default=None)

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "PollBase":
        """Create a poll from a pyrogram message"""
        try:
            assert message.poll
        except AssertionError as e:
            raise PyrogramConversionError("Message is not a poll") from e

        return cls(
            chat_id=message.chat.id,
            message_id=message.id,
            question=message.poll.question,
            poll_type=PollType.POLL,
            is_anonymous=message.poll.is_anonymous,
            close_date=message.poll.close_date,
        )


class PollOptionsBase(BaseSchema):
    poll_id: int = Field(foreign_key="polls.object_id")
    option_text: str = Field(min_length=1, max_length=100)

    @classmethod
    async def from_pyrogram(
        cls, poll_id: int, option_position: int, message: Message
    ) -> "PollOptionsBase":
        """Create a poll option from a pyrogram message"""
        try:
            assert message.poll
            assert option_position
            assert isinstance(option_position, int)
            assert option_position < len(message.poll.options)
            assert option_position >= 0
        except AssertionError as e:
            raise PyrogramConversionError(
                f"Error creating poll option from pyrogram message: {e}"
            ) from e

        return cls(
            poll_id=poll_id,
            option_text=message.poll.options[option_position].text,
        )
