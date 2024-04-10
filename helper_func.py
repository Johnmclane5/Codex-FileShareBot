#(©)Codexbotz

import base64
import re
import asyncio
import aiofiles
import aiohttp
from config import *
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNEL, ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id = FORCE_SUB_CHANNEL, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
        return False
    else:
        return True

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=") # links generated before this commit will be having = sign, hence striping them to handle padding errors.
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes) 
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern,message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


subscribed = filters.create(is_subscribed)

async def download_movie_poster(file_id, movie_name, release_year):
    tmdb_search_url = f'https://api.themoviedb.org/3/search/multi?api_key={TMDB_API_KEY}&query={movie_name}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(tmdb_search_url) as search_response:
                search_data = await search_response.json()

                if search_data['results']:
                    # Filter results based on release year and first air date
                    matching_results = [
                        result for result in search_data['results']
                        if ('release_date' in result and result['release_date'][:4] == str(release_year)) or
                        ('first_air_date' in result and result['first_air_date'][:4] == str(
                            release_year))
                    ]

                    if matching_results:
                        result = matching_results[0]

                        # Fetch additional details using movie ID
                        movie_id = result['id']
                        media_type = result['media_type']

                        tmdb_movie_url = f'https://api.themoviedb.org/3/{media_type}/{movie_id}/images?api_key={TMDB_API_KEY}&language=en-US&include_image_language=en'

                        async with session.get(tmdb_movie_url) as movie_response:
                            movie_data = await movie_response.json()

                        # Use the first backdrop image path from either detailed data or result
                        backdrop_path = None
                        if 'backdrops' in movie_data and movie_data['backdrops']:
                            backdrop_path = movie_data['backdrops'][0]['file_path']
                        elif 'backdrop_path' in result and result['backdrop_path']:
                            backdrop_path = result['backdrop_path']

                        # If both backdrop_path and poster_path are not available, use poster_path
                        if not backdrop_path and 'poster_path' in result and result['poster_path']:
                            poster_path = result['poster_path']
                            poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"

                            async with session.get(poster_url) as poster_response:
                                if poster_response.status == 200:
                                    poster_path = f'poster_{file_id}.jpg'
                                    async with aiofiles.open(poster_path, 'wb') as f:
                                        await f.write(await poster_response.read())
                                        return poster_path
                        elif backdrop_path:
                            backdrop_url = f"https://image.tmdb.org/t/p/original{backdrop_path}"

                            async with session.get(backdrop_url) as backdrop_response:
                                if backdrop_response.status == 200:
                                    poster_path = f'backdrop_{file_id}.jpg'
                                    async with aiofiles.open(poster_path, 'wb') as f:
                                        await f.write(await backdrop_response.read())
                                        return poster_path
                        else:
                            LOGGER(
                                "Failed to obtain backdrop and poster paths from movie_data and result")

                    else:
                        LOGGER(
                            f"No matching results found for movie: {movie_name} ({release_year})")

                else:
                    LOGGER(f"No results found for movie: {movie_name}")

    except Exception as e:
        LOGGER(f"Error fetching TMDB data: {e}")

    return None

async def extract_movie_info(caption):
    try:
        regex = re.compile(r'(.+?)(\d{4})')
        match = regex.search(caption)

        if match:
            movie_name = match.group(1).replace('.', ' ').strip()
            release_year = match.group(2)
            return movie_name, release_year
        
    except Exception as e:
        LOGGER.error(e)

    return None, None
