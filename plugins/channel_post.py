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
from helper_func import encode, extract_movie_info, download_movie_poster
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

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'{shorty}')]])

    await reply_text.edit(f"<b>Here is your link</b>\n\n{shorty}", reply_markup=reply_markup, disable_web_page_preview = True)

    if not DISABLE_CHANNEL_BUTTON:
        await post_message.edit_reply_markup(reply_markup)



@Bot.on_message(filters.channel & filters.incoming & (filters.document | filters.audio | filters.video)  & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    shorty = tiny(shorten_url(link))

    media = message.audio or message.video or message.document or message.photo
    caption = message.caption if message.caption else ""
    if caption:
        file_id = message.id
        movie_name, release_year = await extract_movie_info(caption)
        poster_path = await download_movie_poster(file_id, movie_name, release_year)
    if message.video:
         new_caption = f"<b>{caption}</b> <b>{humanbytes(media.file_size)}</b>\n<b>{shorty}</b>"

    try:
        await asyncio.sleep(5)
               
        await client.send_photo(NEW_CAPTIONS_CHANNEL_ID, photo = poster_path, caption = new_caption)
        os.remove(poster_path)

    except Exception as e: 
        print(e)
        pass


def humanbytes(size):
    # Function to format file size in a human-readable format
    if not size:
        return "0 B"
    # Define byte sizes
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while size >= 1024 and i < len(suffixes) - 1:
        size /= 1024
        i += 1
    f = ('%.2f' % size).rstrip('0').rstrip('.')
    return f"{f} {suffixes[i]}"