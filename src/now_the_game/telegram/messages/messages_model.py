from ...core.base import BaseModel
from .messages_schemas import Message


class MessageModel(BaseModel[Message]):
    def __init__(self):
        super().__init__(Message)


message_model = MessageModel()
