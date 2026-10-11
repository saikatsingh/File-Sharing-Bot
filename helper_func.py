import base64
import re
import asyncio
import io
import aiohttp
from urllib.parse import quote
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import FORCE_SUB_CHANNELS, ADMINS, SHORTLINK_URL, SHORTLINK_API
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait


async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNELS:
        return True

    # Safe user_id detection for both Message and CallbackQuery
    user_id = update.from_user.id if getattr(update, "from_user", None) else None
    if not user_id:
        return True

    if user_id in ADMINS:
        return True
    
    # Protita Force Sub channel ek ek kore check korbe
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
                return False
        except UserNotParticipant:
            return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            pass
            
    return True


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
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
        matches = re.match(pattern, message.text)
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


async def get_shortlink(url: str) -> str:
    if not SHORTLINK_URL or not SHORTLINK_API:
        return url
    
    api_url = f"https://{SHORTLINK_URL}/api?api={SHORTLINK_API}&url={quote(url)}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as response:
                data = await response.json()
                if data.get("status") == "success" or "shortenedUrl" in data:
                    return data.get("shortenedUrl", url)
                return url
    except Exception as e:
        print(f"Shortener API Error: {e}")
        return url


async def get_random_pic(api_url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(api_url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, dict):
                        if "url" in data:
                            return data["url"]
                        elif "images" in data and len(data["images"]) > 0:
                            return data["images"][0].get("url", api_url)
                        elif "results" in data and len(data["results"]) > 0:
                            return data["results"][0].get("url", api_url)
    except Exception as e:
        print(f"Error fetching API image URL: {e}")
    return api_url


async def get_random_pic_data(api_url: str):
    """
    Direct graph.org / telegra.ph link othoba anime API endpoints theke
    image memory buffer-e (io.BytesIO) load kore return kore.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            target_url = api_url
            
            # 1. API endpoint hole JSON theke URL neoa
            if "nekos.best" in api_url:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("results") and len(data["results"]) > 0:
                            target_url = data["results"][0].get("url", api_url)
            elif "api.waifu.im" in api_url:
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("images") and len(data["images"]) > 0:
                            target_url = data["images"][0].get("url", api_url)
            elif "api.waifu.pics" in api_url or api_url.endswith("/neko") or api_url.endswith("/waifu"):
                async with session.get(api_url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict) and "url" in data:
                            target_url = data["url"]

            # 2. Binary buffer download kora
            async with session.get(target_url, timeout=8) as img_resp:
                if img_resp.status == 200:
                    img_bytes = await img_resp.read()
                    buffer = io.BytesIO(img_bytes)
                    buffer.name = "start_pic.jpg"
                    return buffer
                else:
                    print(f"Image download status: {img_resp.status} for {target_url}")
    except Exception as e:
        print(f"Failed to fetch image buffer: {e}")
        
    return None


subscribed = filters.create(is_subscribed)
