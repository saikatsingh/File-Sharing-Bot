import os
import asyncio
import logging
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from bot import Bot
from config import ADMINS, CHANNEL_ID, MAIN_CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

logger = logging.getLogger(__name__)


# Shob dhoroner Bot Commands exclude kora holo jate link generate na hoy
EXCLUDED_COMMANDS = [
    'start', 'help', 'myplan', 'plans', 'buy', 'premium', 
    'users', 'broadcast', 'batch', 'genlink', 'stats', 
    'add_premium', 'remove_premium'
]


@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(EXCLUDED_COMMANDS))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
    except Exception as e:
        logger.error(f"Error copying post in private: {e}")
        await reply_text.edit_text("Something Went Wrong..!")
        return

    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    bot_uname = client.username or (await client.get_me()).username
    link = f"https://t.me/{bot_uname}?start={base64_string}"

    admin_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Get File Link", url=link)],
        [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
    ])

    await reply_text.edit(f"<b>Here Is Your Link</b>\n\n{link}", reply_markup=admin_markup, disable_web_page_preview=True)

    if not DISABLE_CHANNEL_BUTTON:
        channel_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Get File / Download Link", url=link)]
        ])
        try:
            await post_message.edit_reply_markup(channel_markup)
        except Exception as e:
            logger.error(f"Error adding button to copied message: {e}")


# MAIN_CHANNEL_ID (Public Channel) e video ashle eti trigger hobe
@Bot.on_message(filters.channel & filters.incoming & filters.chat(MAIN_CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    media = message.video or message.document
    if not media:
        return

    try:
        # 1. Public Channel theke Private DB Channel (client.db_channel.id) e copy kora
        try:
            db_msg = await message.copy(chat_id=client.db_channel.id, disable_notification=True)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            db_msg = await message.copy(chat_id=client.db_channel.id, disable_notification=True)

        # 2. Database Channel ID diye shothik link toiri
        converted_id = db_msg.id * abs(client.db_channel.id)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        bot_uname = client.username or (await client.get_me()).username
        link = f"https://t.me/{bot_uname}?start={base64_string}"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Download / Get File", url=link)]
        ])

        # 3. Caption toiri
        file_name = getattr(media, "file_name", None) or "Media File"
        caption = message.caption.html if message.caption else f"🎬 <b>File:</b> <code>{file_name}</code>"

        # 4. Thumbnail download kore Public Channel e send kora
        photo_sent = False
        if media.thumbs:
            thumb_path = None
            try:
                thumb_path = await client.download_media(media.thumbs[0].file_id)
                if thumb_path and os.path.exists(thumb_path):
                    await client.send_photo(
                        chat_id=message.chat.id,
                        photo=thumb_path,
                        caption=caption,
                        reply_markup=reply_markup
                    )
                    photo_sent = True
            except Exception as e:
                logger.error(f"Failed to download/send thumbnail: {e}")
            finally:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)

        if not photo_sent:
            await client.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        # 5. Public Channel theke original boro video remove kora
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete original video: {e}")

    except Exception as e:
        logger.error(f"Error in auto replace workflow: {e}", exc_info=True)
