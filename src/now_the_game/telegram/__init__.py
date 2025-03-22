"""
Telegram module initialization
"""

# Re-export repositories for easier imports
from .chats.chats_model import chat_model
from .messages.messages_model import message_model
from .polls.polls_model import poll_options_model, poll_model

# Re-export schemas for convenience
from .telegram_schemas import (
    ChatSchema,
    ChatMembershipSchema,
    MessageSchema,
    PollSchema,
    PollOptionSchema,
    UserSchema,
)
from .users.users_model import user_model
