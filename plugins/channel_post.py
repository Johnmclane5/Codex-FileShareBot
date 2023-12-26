#(©)Codexbotz

import os
import asyncio
import aiohttp
import requests
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON, NEW_CAPTIONS_CHANNEL_ID
from helper_func import encode
from plugins.shorty import shorten_url, tiny

@Bot.on_message(filters.private & filters.user(ADMINS) & (filters.document | filters.audio |filters.video))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote = True)
    try:
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    shorty = tiny(shorten_url(link))

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Get File", url=f'{shorty}')]])

    await reply_text.edit(f"<b>Here is your link</b>\n\n{shorty}", reply_markup=reply_markup, disable_web_page_preview = True)

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)



@Bot.on_message(filters.channel & filters.incoming & (filters.document | filters.audio | filters.video)  & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    shorty = tiny(shorten_url(link))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Send in DM", url=f'{shorty}')]])
    
    try:
        await message.edit_reply_markup(reply_markup)             
    except Exception as e: 
        print(e)
        pass
