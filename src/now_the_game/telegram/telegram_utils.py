from pyrogram.types import Message, Poll


def is_poll(message: Message) -> bool:
    return message.poll is not None


def get_poll(message: Message) -> Poll:
    if not is_poll(message):
        raise ValueError("Message is not a poll")
    return message.poll
