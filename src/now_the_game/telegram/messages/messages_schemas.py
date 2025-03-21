"""
Message-specific schema definitions.
This module re-exports the Message-related schemas from the central schema module.
"""

from datetime import datetime

import numpy as np
from pydantic import BaseModel, Field
from pyrogram.enums import MessageEntityType, MessageMediaType
from pyrogram.types import Message

from ... import logger
from ..telegram_schemas import Message as MessageSchema
from ..telegram_schemas import MessageBase


class ChatMessageEngagement(BaseModel):
    message_id: int = Field(..., description="ID of the message")
    first_name: str | None = Field(None, description="First name of the sender")
    username: str | None = Field(None, description="Username of the sender")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Timestamp of the message")

    # Link preview
    link_preview_title: str | None = Field(
        None, description="Title of the link preview"
    )
    link_preview_description: str | None = Field(
        None, description="Description of the link preview"
    )

    # Negative scores
    is_self: bool = Field(False, description="Whether the message is from the user")
    is_bot: bool = Field(False, description="Whether the message is from a bot")

    # Positive scores
    is_premium: bool = Field(
        False, description="Whether the message is from a premium user"
    )

    has_mention: bool = Field(
        False, description="Whether the message mentions the user"
    )
    has_link: bool = Field(False, description="Whether the message has a link")

    reaction_count: int = Field(0, description="Number of reactions on the message")
    media_score: int = Field(0, description="Score of the media in the message")

    @property
    def engagement_score(self) -> float:
        """
        Calculate the engagement score of the message
        """
        # --- 1. Feature Preparation (with non-linear transformations) ---

        # Length (using log1p for a smoother curve)
        link_title_length = (
            len(self.link_preview_title) if self.link_preview_title else 0
        )
        link_description_length = (
            len(self.link_preview_description) if self.link_preview_description else 0
        )
        combined_message_length = (
            len(self.message) + link_title_length + link_description_length
        )
        length_score = np.log1p(combined_message_length)

        # Penalize VERY short messages, but still allow for reasonably short ones.
        if combined_message_length < 20:  # Less than ~5 words
            length_score = 0.1  # Small, but non-zero
        else:
            length_score = np.log1p(combined_message_length) / 5.0  # Scale down the log
            length_score = min(length_score, 1.0)  # Limit maximum

        # Reactions (using a modified sigmoid - sharper increase initially)
        reaction_score = 1 / (
            1 + np.exp(-(self.reaction_count - 1) / 2)
        )  # Shift and scale

        # --- 2. Feature Engineering (Interaction Terms) ---
        # TODO: Add later -- it's not that important rn

        # --- 3. Weighted Sum (Weights Optimized for Conversation Importance) ---
        score = (
            0.3 * length_score  # Moderate weight on length (substance)
            - 5.0 * float(self.is_self)  # STRONG penalty for self-messages
            - 3.0 * float(self.is_bot)  # Strong penalty for bot messages (usually)
            + 1.0 * reaction_score  # HIGH weight on reactions (discussion indicator)
            + 0.2
            * float(
                self.is_premium
            )  # Small bonus for premium users (might have higher status)
            + 0.1
            * float(
                self.has_mention
            )  # Small bonus for mentions (targeted conversation)
            + 0.4
            * float(self.has_link)  # Moderate bonus for links (potential information)
            + 0.5 * self.media_score  # Moderate weight on media score (if available)
        )

        # --- 4. Normalization (Min-Max, with adjusted bounds) ---
        # We'll adjust the bounds to reflect the new weights and penalties.
        MIN_SCORE = -5.0  # is_self = True is the main negative driver
        MAX_SCORE = 3.0  # Assuming good length, reactions, and maybe media/link.
        normalized_score = (score - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)

        # Clip to 0-1 range, but favor higher scores.
        normalized_score = np.clip(normalized_score, 0.0, 1.0)

        return normalized_score

    @classmethod
    def extract_message_info(cls, message_object: Message):  # noqa: C901
        try:
            message_id = message_object.id
            # We don't handle non-text messages for now
            message = message_object.text
            first_name = message_object.from_user.first_name
            username = message_object.from_user.username
            timestamp = message_object.date

            if message_object.web_page is not None:
                link_preview_title = message_object.web_page.title
                link_preview_description = message_object.web_page.description
            else:
                link_preview_title = None
                link_preview_description = None

            if message_object.from_user is not None:
                is_self = message_object.from_user.is_self
                is_bot = message_object.from_user.is_bot
                is_premium = message_object.from_user.is_premium
            else:
                is_self = False
                is_bot = False
                is_premium = False

            if message_object.media is not None:
                if message_object.media == MessageMediaType.DOCUMENT:
                    media_score = 1
                elif message_object.media == MessageMediaType.PHOTO:
                    media_score = 2
                elif message_object.media == MessageMediaType.VIDEO:
                    media_score = 3
                elif message_object.media == MessageMediaType.AUDIO:
                    media_score = 4
                else:
                    media_score = 0
            else:
                media_score = 0

            has_mention = False
            has_link = False
            if message_object.entities is not None:
                for entity in message_object.entities:
                    if entity.type == MessageEntityType.MENTION:
                        has_mention = True
                    if entity.type == MessageEntityType.URL:
                        has_link = True

            reaction_count = 0
            if message_object.reactions is not None:
                for reaction in message_object.reactions.reactions:
                    reaction_count += reaction.count

            return cls(
                message_id=message_id,
                first_name=first_name,
                username=username,
                message=message,
                timestamp=timestamp,
                link_preview_title=link_preview_title,
                link_preview_description=link_preview_description,
                is_self=is_self,
                is_bot=is_bot,
                is_premium=is_premium,
                has_mention=has_mention,
                has_link=has_link,
                reaction_count=reaction_count,
                media_score=media_score,
            )
        except Exception as e:
            logger.error(f"Error extracting chat message info: {e}")
            return None
