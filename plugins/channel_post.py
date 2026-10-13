import os
import asyncio
import logging
from pyrogram import filters, Client
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, 
    InputMediaPhoto, CallbackQuery
)
from pyrogram.errors import FloodWait
from bot import Bot
from config import ADMINS, CHANNEL_ID, MAIN_CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

logger = logging.getLogger(__name__)

# Track thumb editing state in admin PM
THUMB_PROCESS = {}

# Media Group / Batch Buffers
MEDIA_GROUP_CACHE = {}
ALBUM_LOCKS = {}

# Shob dhoroner Bot Commands exclude kora holo jate link generate na hoy
EXCLUDED_COMMANDS = [
    'start', 'help', 'myplan', 'plans', 'buy', 'premium', 
    'users', 'broadcast', 'batch', 'genlink', 'stats', 
    'add_premium', 'remove_premium', 'thumb'
]


# --- 1. CHANNEL E POST ER REPLY TE /thumb COMMAND ---
@Bot.on_message(filters.chat(MAIN_CHANNEL_ID) & filters.command('thumb'))
async def thumb_command_channel(client: Client, message: Message):
    if not message.reply_to_message:
        k = await message.reply_text("❌ Please reply to the post whose thumbnail you want to change!")
        await asyncio.sleep(5)
        try:
            await message.delete()
            await k.delete()
        except Exception:
            pass
        return

    target_msg = message.reply_to_message
    if not (target_msg.photo or target_msg.document or target_msg.video):
        k = await message.reply_text("❌ The replied message does not have any media!")
        await asyncio.sleep(5)
        try:
            await message.delete()
            await k.delete()
        except Exception:
            pass
        return

    # Delete the /thumb trigger message from channel to keep channel clean
    try:
        await message.delete()
    except Exception:
        pass

    # Save target message context for Admin
    for admin_id in ADMINS:
        THUMB_PROCESS[admin_id] = {
            "channel_id": message.chat.id,
            "message_id": target_msg.id,
            "original_caption": target_msg.caption.html if target_msg.caption else "",
            "reply_markup": target_msg.reply_markup,
            "step": "waiting_photo"
        }
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_thumb_edit")]])
        try:
            await client.send_message(
                chat_id=admin_id,
                text=f"🖼 <b>Change Thumbnail Request</b>\n\nTarget Post ID: <code>{target_msg.id}</code> in channel.\n\n👉 <b>Please send the new image/photo now.</b>",
                reply_markup=cancel_btn
            )
        except Exception as e:
            logger.error(f"Failed to message admin {admin_id}: {e}")


# --- 2. ADMIN PRIVATE CHAT E THUMBNAIL PHOTO & CAPTION RECEIVE KORA ---
@Bot.on_message(filters.private & filters.user(ADMINS) & (filters.photo | filters.text) & ~filters.command(EXCLUDED_COMMANDS))
async def handle_admin_thumb_input(client: Client, message: Message):
    admin_id = message.from_user.id
    if admin_id not in THUMB_PROCESS:
        return

    process = THUMB_PROCESS[admin_id]
    step = process.get("step")

    # Step A: Admin sent Photo
    if step == "waiting_photo":
        if not message.photo:
            await message.reply_text("⚠️ Please send an image/photo for the thumbnail!")
            return

        process["photo_file_id"] = message.photo.file_id
        process["step"] = "waiting_caption"

        skip_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Keep Original Caption", callback_data="skip_caption_edit")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_thumb_edit")]
        ])

        await message.reply_text(
            "✅ <b>Image received!</b>\n\nNow send the <b>New Caption</b> for this post, or tap <b>Keep Original Caption</b> below to leave it as it was.",
            reply_markup=skip_btn
        )
        return

    # Step B: Admin sent Text Caption
    elif step == "waiting_caption":
        new_caption = message.text.html if message.text else process["original_caption"]
        await apply_new_thumbnail(client, admin_id, new_caption)


# --- 3. APPLY NEW THUMBNAIL & CAPTION TO CHANNEL POST ---
async def apply_new_thumbnail(client: Client, admin_id: int, final_caption: str):
    if admin_id not in THUMB_PROCESS:
        return

    process = THUMB_PROCESS.pop(admin_id)
    channel_id = process["channel_id"]
    msg_id = process["message_id"]
    photo_file_id = process["photo_file_id"]
    reply_markup = process["reply_markup"]

    try:
        await client.edit_message_media(
            chat_id=channel_id,
            message_id=msg_id,
            media=InputMediaPhoto(media=photo_file_id, caption=final_caption),
            reply_markup=reply_markup
        )
        await client.send_message(
            chat_id=admin_id,
            text=f"🎉 <b>Success!</b>\n\nThe post in channel (ID: <code>{msg_id}</code>) has been updated with the new thumbnail and caption."
        )
    except Exception as e:
        logger.error(f"Failed to edit channel post: {e}")
        await client.send_message(
            chat_id=admin_id,
            text=f"❌ <b>Failed to update post!</b>\n\nError: <code>{e}</code>"
        )


# --- 4. CALLBACKS: SKIP CAPTION & CANCEL ---
@Bot.on_callback_query(filters.regex('^skip_caption_edit$'))
async def skip_caption_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if admin_id not in THUMB_PROCESS:
        await query.answer("No active thumbnail change session!", show_alert=True)
        return

    await query.answer()
    await query.message.edit_text("⏳ Updating post with original caption...")
    original_caption = THUMB_PROCESS[admin_id]["original_caption"]
    await apply_new_thumbnail(client, admin_id, original_caption)


@Bot.on_callback_query(filters.regex('^cancel_thumb_edit$'))
async def cancel_thumb_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if admin_id in THUMB_PROCESS:
        THUMB_PROCESS.pop(admin_id)

    await query.answer("Cancelled!")
    await query.message.edit_text("❌ Thumbnail change cancelled.")


# --- 5. PRIVATE ADMIN MESSAGE DB UPLOAD (NORMAL WORKFLOW) ---
@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(EXCLUDED_COMMANDS))
async def channel_post(client: Client, message: Message):
    if message.from_user.id in THUMB_PROCESS:
        return

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


# --- 6. PUBLIC CHANNEL AUTO REPLACE & BATCH PROCESSOR ---
async def process_batch_files(client: Client, channel_id: int, messages_list: list):
    """Multiple videos ke DB channel-e pathiye ekta Batch link toiri kore"""
    if not messages_list:
        return

    copied_ids = []
    first_thumb_file_id = None
    common_caption = None

    for msg in messages_list:
        media = msg.video or msg.document
        if not media:
            continue
        if not first_thumb_file_id and media.thumbs:
            first_thumb_file_id = media.thumbs[0].file_id
        if not common_caption and msg.caption:
            common_caption = msg.caption.html

        try:
            db_msg = await msg.copy(chat_id=client.db_channel.id, disable_notification=True)
            copied_ids.append(db_msg.id)
        except FloodWait as e:
            await asyncio.sleep(e.x)
            db_msg = await msg.copy(chat_id=client.db_channel.id, disable_notification=True)
            copied_ids.append(db_msg.id)
        except Exception as e:
            logger.error(f"Error copying batch media: {e}")

    if not copied_ids:
        return

    bot_uname = client.username or (await client.get_me()).username
    db_channel_id = abs(client.db_channel.id)

    if len(copied_ids) == 1:
        single_id = copied_ids[0] * db_channel_id
        string = f"get-{single_id}"
        btn_text = "📥 Download File"
        def_cap = common_caption or "🎬 <b>Video File Attached</b>"
    else:
        first_id = min(copied_ids) * db_channel_id
        last_id = max(copied_ids) * db_channel_id
        string = f"get-{first_id}-{last_id}"
        btn_text = f"📦 Download Batch Files ({len(copied_ids)} Videos)"
        def_cap = common_caption or f"📦 <b>Batch Collection ({len(copied_ids)} Files)</b>"

    base64_string = await encode(string)
    link = f"https://t.me/{bot_uname}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, url=link)]
    ])

    photo_sent = False
    if first_thumb_file_id:
        thumb_path = None
        try:
            thumb_path = await client.download_media(first_thumb_file_id)
            if thumb_path and os.path.exists(thumb_path):
                await client.send_photo(
                    chat_id=channel_id,
                    photo=thumb_path,
                    caption=def_cap,
                    reply_markup=reply_markup
                )
                photo_sent = True
        except Exception as e:
            logger.error(f"Failed to send thumbnail: {e}")
        finally:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

    if not photo_sent:
        await client.send_message(
            chat_id=channel_id,
            text=def_cap,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    for msg in messages_list:
        try:
            await msg.delete()
        except Exception:
            pass


@Bot.on_message(filters.channel & filters.incoming & filters.chat(MAIN_CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    media = message.video or message.document
    if not media:
        return

    group_id = message.media_group_id

    # 1. Multiple video eksathe ashle (Album/Media group)
    if group_id:
        if group_id not in MEDIA_GROUP_CACHE:
            MEDIA_GROUP_CACHE[group_id] = []
        MEDIA_GROUP_CACHE[group_id].append(message)

        if group_id not in ALBUM_LOCKS:
            ALBUM_LOCKS[group_id] = True
            await asyncio.sleep(3.5)
            msgs = MEDIA_GROUP_CACHE.pop(group_id, [])
            ALBUM_LOCKS.pop(group_id, None)
            if msgs:
                await process_batch_files(client, message.chat.id, msgs)
        return

    # 2. Single video
    await process_batch_files(client, message.chat.id, [message])
