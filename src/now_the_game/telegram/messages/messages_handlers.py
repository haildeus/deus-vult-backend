from pyrogram import Client, filters
from pyrogram.types import Message
from ... import logger


@Client.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("Hello, world!")


@Client.on_message(filters.command("help"))
async def help(client: Client, message: Message):
    await message.reply_text("Help message")
