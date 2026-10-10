import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from bot import Bot
from config import ADMINS, CHANNEL_ID, DB_CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode


@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(['start', 'users', 'broadcast', 'batch', 'genlink', 'stats']))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote=True)
    try:
        post_message = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)
    except Exception as e:
        print(f"Error copying post: {e}")
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
            print(f"Error adding button: {e}")


@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):
    if DISABLE_CHANNEL_BUTTON:
        return

    # শুধুমাত্র ভিডিও বা ডকুমেন্টের ক্ষেত্রে চলবে
    if not (message.video or message.document):
        return

    try:
        # ১. মেইন চ্যানেল থেকে আসল ফাইলটি Private DB Channel-এ কপি করা
        db_msg = await message.copy(chat_id=DB_CHANNEL_ID, disable_notification=True)

        # ২. DB চ্যানেলের মেসেজ আইডি দিয়ে লিংক তৈরি
        converted_id = db_msg.id * abs(DB_CHANNEL_ID)
        string = f"get-{converted_id}"
        base64_string = await encode(string)
        link = f"https://t.me/{client.username}?start={base64_string}"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Download / Get File", url=link)]
        ])

        # ৩. ক্যাপশন তৈরি করা
        file_name = ""
        if message.video and message.video.file_name:
            file_name = message.video.file_name
        elif message.document and message.document.file_name:
            file_name = message.document.file_name

        caption = message.caption.html if message.caption else f"<b>📁 File:</b> <code>{file_name}</code>"

        # ৪. থাম্বনেইল সংগ্রহ করা
        thumbnail = None
        if message.video and message.video.thumbs:
            thumbnail = message.video.thumbs[0].file_id
        elif message.document and message.document.thumbs:
            thumbnail = message.document.thumbs[0].file_id

        # ৫. মেইন চ্যানেলে থাম্বনেইল ফটো ও বাটন পোস্ট করা
        if thumbnail:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=caption,
                reply_markup=reply_markup
            )

        # ৬. মেইন চ্যানেল থেকে আসল বড় ভিডিওটি ডিলিট করে দেওয়া
        await message.delete()

    except FloodWait as e:
        await asyncio.sleep(e.x)
    except Exception as e:
        print(f"Error in auto replace workflow: {e}")
