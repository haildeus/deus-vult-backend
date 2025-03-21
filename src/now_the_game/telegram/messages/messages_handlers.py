from pyrogram import Client, filters

from ... import logger


@Client.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("Hello, world!")


@Client.on_message(filters.command("help"))
async def help(client, message):
    await message.reply_text("Help message")
