import os
import re
import asyncio
import logging
from PIL import Image
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
THUMB_MEDIA_LOCKS = {}

# Channel-wide Sliding Batch Queue
CHANNEL_QUEUE = {}
CHANNEL_LOCKS = {}

# Shob dhoroner Bot Commands exclude kora holo jate link generate na hoy
EXCLUDED_COMMANDS = [
    'start', 'help', 'myplan', 'plans', 'buy', 'premium', 
    'users', 'broadcast', 'batch', 'genlink', 'stats', 'status',
    'add_premium', 'remove_premium', 'thumb', 'ban', 'unban', 'cleardb'
]


def clean_external_caption(caption: str) -> str:
    """Caption theke shob external links, usernames ebong hyperlinks remove kore"""
    if not caption:
        return ""
    
    text = re.sub(r'<a\s+(?:[^>]*?\s+)?href="[^"]*"[^>]*>(.*?)</a>', r'\1', caption, flags=re.IGNORECASE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+|t\.me/\S+|telegram\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    
    lines = [line.strip() for line in text.splitlines()]
    clean_text = "\n".join([line for line in lines if line])
    return clean_text.strip()


def create_image_collage(image_paths: list) -> str:
    """Multiple images ke vertically jora lagie 1-ti collage image toiri kore"""
    if len(image_paths) == 1:
        return image_paths[0]

    images = [Image.open(p) for p in image_paths]
    
    target_width = images[0].width
    resized_images = []
    total_height = 0

    for img in images:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        w_percent = target_width / float(img.width)
        h_size = int(float(img.height) * float(w_percent))
        img_resized = img.resize((target_width, h_size), Image.Resampling.LANCZOS)
        resized_images.append(img_resized)
        total_height += h_size

    collage = Image.new('RGB', (target_width, total_height))
    y_offset = 0
    for img in resized_images:
        collage.paste(img, (0, y_offset))
        y_offset += img.height

    collage_path = "downloads/collage_thumb.jpg"
    os.makedirs("downloads", exist_ok=True)
    collage.save(collage_path, format="JPEG", quality=90)
    return collage_path


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

    try:
        await message.delete()
    except Exception:
        pass

    for admin_id in ADMINS:
        THUMB_PROCESS[admin_id] = {
            "channel_id": message.chat.id,
            "message_id": target_msg.id,
            "original_caption": target_msg.caption.html if target_msg.caption else "",
            "reply_markup": target_msg.reply_markup,
            "step": "waiting_photo",
            "photos_received": []
        }
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_thumb_edit")]])
        try:
            await client.send_message(
                chat_id=admin_id,
                text=f"🖼 <b>Change Thumbnail Request</b>\n\nTarget Post ID: <code>{target_msg.id}</code> in channel.\n\n👉 <b>Please send the new image/photos now.</b> (1, 2, or 3 images)",
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

    # Step A: Photo(s)
    if step == "waiting_photo":
        if not message.photo:
            await message.reply_text("⚠️ Please send an image/photo for the thumbnail!")
            return

        process["photos_received"].append(message)

        if admin_id in THUMB_MEDIA_LOCKS:
            return

        THUMB_MEDIA_LOCKS[admin_id] = True
        await asyncio.sleep(3.0)
        THUMB_MEDIA_LOCKS.pop(admin_id, None)

        received_msgs = process.get("photos_received", [])
        if not received_msgs:
            return

        msg_wait = await message.reply_text("⏳ Processing images...")
        downloaded_paths = []

        for p_msg in received_msgs:
            try:
                p_path = await client.download_media(p_msg.photo.file_id)
                if p_path and os.path.exists(p_path):
                    downloaded_paths.append(p_path)
            except Exception as e:
                logger.error(f"Error downloading admin thumb: {e}")

        if not downloaded_paths:
            await msg_wait.edit_text("❌ Failed to process images. Please try again.")
            return

        final_thumb_file = create_image_collage(downloaded_paths)
        process["final_local_image"] = final_thumb_file
        process["temp_files_to_clean"] = downloaded_paths
        process["step"] = "waiting_caption"

        await msg_wait.delete()

        skip_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Keep Original Caption", callback_data="skip_caption_edit")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_thumb_edit")]
        ])

        count_text = f"{len(downloaded_paths)} images combined into 1 collage!" if len(downloaded_paths) > 1 else "Image received!"

        await message.reply_text(
            f"✅ <b>{count_text}</b>\n\nNow send the <b>New Caption</b> for this post, or tap <b>Keep Original Caption</b> below to leave it as it was.",
            reply_markup=skip_btn
        )
        return

    # Step B: Text Caption
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
    final_local_image = process.get("final_local_image")
    temp_files = process.get("temp_files_to_clean", [])
    reply_markup = process["reply_markup"]

    try:
        await client.edit_message_media(
            chat_id=channel_id,
            message_id=msg_id,
            media=InputMediaPhoto(media=final_local_image, caption=final_caption),
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
    finally:
        for p in temp_files:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        if final_local_image and os.path.exists(final_local_image) and final_local_image not in temp_files:
            try:
                os.remove(final_local_image)
            except Exception:
                pass


# --- 4. CALLBACKS: SKIP CAPTION & CANCEL ---
@Bot.on_callback_query(filters.regex('^skip_caption_edit$'))
async def skip_caption_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if admin_id not in THUMB_PROCESS:
        await query.answer("No active session!", show_alert=True)
        return

    await query.answer()
    await query.message.edit_text("⏳ Updating post with original caption...")
    original_caption = THUMB_PROCESS[admin_id]["original_caption"]
    await apply_new_thumbnail(client, admin_id, original_caption)


@Bot.on_callback_query(filters.regex('^cancel_thumb_edit$'))
async def cancel_thumb_callback(client: Client, query: CallbackQuery):
    admin_id = query.from_user.id
    if admin_id in THUMB_PROCESS:
        process = THUMB_PROCESS.pop(admin_id)
        for p in process.get("temp_files_to_clean", []):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

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


# --- 6. BATCH WORKFLOW CORE EXECUTION ---
async def process_batch_files(client: Client, channel_id: int, messages_list: list):
    """Multiple media (video, photo, document, audio) ke DB channel-e pathiye ekta Batch link toiri kore"""
    if not messages_list:
        return

    copied_ids = []
    first_thumb_file_id = None
    common_caption = None

    for msg in messages_list:
        media = msg.video or msg.document or msg.photo or msg.audio
        if not media:
            continue

        if not first_thumb_file_id:
            if msg.photo:
                first_thumb_file_id = msg.photo.file_id
            elif getattr(media, "thumbs", None):
                first_thumb_file_id = media.thumbs[0].file_id

        if not common_caption and msg.caption:
            common_caption = clean_external_caption(msg.caption.html)

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
        def_cap = common_caption if common_caption else "🎬 <b>Media File Attached</b>"
    else:
        first_id = min(copied_ids) * db_channel_id
        last_id = max(copied_ids) * db_channel_id
        string = f"get-{first_id}-{last_id}"
        btn_text = f"📦 Download Batch Files ({len(copied_ids)} Files)"
        def_cap = common_caption if common_caption else f"📦 <b>Batch Collection ({len(copied_ids)} Files)</b>"

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


# --- 7. AUTO REPLACE WORKFLOW (PUBLIC CHANNEL INCOMING POSTS) ---
@Bot.on_message(filters.chat(MAIN_CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    if message.text and message.text.startswith('/'):
        return

    has_media = bool(message.video or message.document or message.photo or message.audio)
    if not has_media:
        return

    channel_id = message.chat.id

    if channel_id not in CHANNEL_QUEUE:
        CHANNEL_QUEUE[channel_id] = []
    
    CHANNEL_QUEUE[channel_id].append(message)

    if channel_id in CHANNEL_LOCKS:
        return

    CHANNEL_LOCKS[channel_id] = True
    
    await asyncio.sleep(5.0)

    msgs = CHANNEL_QUEUE.pop(channel_id, [])
    CHANNEL_LOCKS.pop(channel_id, None)

    if msgs:
        await process_batch_files(client, channel_id, msgs)
