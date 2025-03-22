from pyrogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.base import BaseModel
from ..telegram_schemas import (
    MessageCore,
    MessageBase,
    ChatBase,
    UserBase,
    UserChatLinkBase,
    ChatMembershipBase,
)
from ... import logger
from ..telegram_exceptions import PyrogramConversionError


class MessageModel(BaseModel[MessageBase]):
    def __init__(self):
        super().__init__(MessageBase)
