from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pyrogram.types import Message, PollOption
from sqlmodel import Field, Relationship

from src.now_the_game.telegram.telegram_exceptions import PyrogramConversionError
from src.shared.base import BaseSchema
from src.shared.events import EventPayload

if TYPE_CHECKING:
    from src.now_the_game.telegram.chats.chats_schemas import ChatTable
    from src.now_the_game.telegram.messages.messages_schemas import MessageTable


class PollType(Enum):
    QUIZ = "quiz"
    POLL = "poll"


"""
MODELS
"""


class SendPollEventPayload(EventPayload):
    chat_id: int | str
    question: str
    options: list[str]
    is_anonymous: bool
    explanation: str | None
    save: bool


"""
TABLES
"""


class PollBase(BaseSchema):
    chat_id: int = Field(foreign_key="chats.object_id", index=True)
    message_id: int = Field(foreign_key="messages.object_id", index=True)
    question: str = Field(min_length=1, max_length=300)
    poll_type: PollType = Field(default=PollType.POLL)
    is_anonymous: bool = Field(default=True)
    close_date: datetime | None = Field(default=None)
    explanation: str | None = Field(default=None)


class PollOptionsBase(BaseSchema):
    poll_id: int = Field(foreign_key="polls.object_id", index=True)
    option_text: str = Field(min_length=1, max_length=100)
    votes: int = Field(default=0, ge=0)


class PollTable(PollBase, table=True):
    __tablename__ = "polls"

    # --- Relationships ---
    options: list["PollOptionTable"] = Relationship(
        back_populates="poll", sa_relationship_kwargs={"lazy": "selectin"}
    )
    chat: "ChatTable" = Relationship(back_populates="polls")
    message: "MessageTable" = Relationship(back_populates="polls")
    # --- End Relationships ---

    @classmethod
    async def from_pyrogram(cls, message: Message) -> "PollTable":
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


class PollOptionTable(PollOptionsBase, table=True):
    __tablename__ = "poll_options"

    # --- Relationships ---
    poll: "PollTable" = Relationship(back_populates="options")
    # --- End Relationships ---

    @classmethod
    async def from_pyrogram(
        cls, poll_id: int, options: list[PollOption]
    ) -> list["PollOptionTable"]:
        """Create a poll option from a pyrogram message"""
        try:
            assert options
            assert isinstance(options, list)
        except AssertionError as e:
            raise PyrogramConversionError("Options are not a list") from e

        return [
            cls(
                poll_id=poll_id,
                option_text=option.text,
                votes=option.voter_count,
            )
            for option in options
        ]
