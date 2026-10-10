import asyncio
import logging
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from bot import Bot
from config import ADMINS, CHANNEL_ID, DB_CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

logger = logging.getLogger(__name__)

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['start', 'users', 'broadcast', 'batch', 'genlink', 'stats']))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)
    except Exception as e:
        logger.error(f"Error copying post in private: {e}")
        await reply_text.edit_text("Something Went Wrong..!")
        return

    converted_id = post_message.id * abs(DB_CHANNEL_ID)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"

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


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    # Shudhu video ba document hole process korbe
    media = message.video or message.document
    if not media:
        return

    try:
        # 1. Main Channel theke DB Channel-e copy kora
        try:
            db_msg = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            db_msg = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)

        # 2. Secret link generate kora
        converted_id = db_msg.id * abs(DB_CHANNEL_ID)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        bot_uname = client.username or (await client.get_me()).username
        link = f"https://t.me/{bot_uname}?start={base64_string}"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Download / Get File", url=link)]
        ])

        # 3. Caption toiri kora
        file_name = getattr(media, "file_name", None) or "Media File"
        caption = message.caption.html if message.caption else f"🎬 <b>File:</b> <code>{file_name}</code>"

        # 4. Thumbnail check kora
        thumb_file_id = None
        if media.thumbs:
            thumb_file_id = media.thumbs[0].file_id

        # 5. Main Channel-e thumbnail ba text post pathano
        posted = False
        if thumb_file_id:
            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=thumb_file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
                posted = True
            except Exception as e:
                logger.warning(f"Failed to send thumbnail photo directly ({e}), sending message instead.")

        if not posted:
            await client.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        # 6. Main Channel theke original boro video-ti delete kora
        try:
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete original video (Check 'Delete Messages' admin permission): {e}")

    except Exception as e:
        logger.error(f"Error in auto replace workflow: {e}", exc_info=True)
