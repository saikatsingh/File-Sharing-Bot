import os, asyncio, humanize, random
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import (
    ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, 
    PROTECT_CONTENT, FILE_AUTO_DELETE, IS_VERIFY, SHORTLINK_URL, SHORTLINK_API, VERIFY_TUTORIAL,
    VERIFY_EXPIRE, FORCE_SUB_CHANNELS, START_PICS
)
from helper_func import subscribed, is_subscribed, encode, decode, get_messages, get_shortlink, get_random_pic_data
from database.database import (
    add_user, del_user, full_userbase, present_user, 
    is_user_verified, update_verify_status, get_verify_token, set_verified
)

file_auto_delete = humanize.naturaldelta(FILE_AUTO_DELETE)
verify_expire_time = humanize.naturaldelta(VERIFY_EXPIRE)


async def send_styled_start(client: Client, message: Message):
    buttons = []
    
    # 1. Force Sub Channel join buttons
    for idx, channel_id in enumerate(FORCE_SUB_CHANNELS, start=1):
        try:
            chat = await client.get_chat(channel_id)
            invite_link = chat.invite_link or await client.export_chat_invite_link(channel_id)
            buttons.append([InlineKeyboardButton(text=f"👉 Join Channel {idx} 👈", url=invite_link)])
        except Exception as e:
            print(f"Error getting invite link for channel {channel_id}: {e}")

    # 2. Interactive Verify Button (Callback)
    buttons.append([InlineKeyboardButton(text='🔄 Try Again / Verify', callback_data='check_verification')])

    # 3. Custom text message (English)
    user_name = message.from_user.first_name if message.from_user else "User"
    bot_username = client.username or (await client.get_me()).username

    caption_text = f"""Hey {user_name}
Welcome to @{bot_username}

🥵🥵Join Below Channels And Tap Verify To Continue 🍑🍑"""

    # 4. Direct URL or Memory Buffer Image
    raw_url = random.choice(START_PICS) if START_PICS else None
    
    if raw_url:
        if raw_url.startswith("http") and (raw_url.endswith(".jpg") or raw_url.endswith(".png") or "graph.org" in raw_url or "telegra.ph" in raw_url):
            try:
                await message.reply_photo(
                    photo=raw_url,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    quote=True
                )
                return
            except Exception as e:
                print(f"Direct photo send failed, trying buffer fallback: {e}")

        photo_buffer = await get_random_pic_data(raw_url)
        if photo_buffer:
            try:
                await message.reply_photo(
                    photo=photo_buffer,
                    caption=caption_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    quote=True
                )
                return
            except Exception as e:
                print(f"Buffer photo send failed: {e}")

    await message.reply_text(
        text=caption_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        quote=True,
        disable_web_page_preview=True
    )


@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    if not await present_user(user_id):
        try:
            await add_user(user_id)
        except:
            pass

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return

        # --- 1. Token Verification Process ---
        if base64_string.startswith("verify_"):
            token = base64_string.split("verify_", 1)[1]
            saved_token = await get_verify_token(user_id)
            if saved_token and saved_token == token:
                await set_verified(user_id)
                await message.reply_text(
                    f"<b>✅ Token Successfully Verified!</b>\n\n"
                    f"You now have unrestricted access for the next <b>{verify_expire_time}</b>. You can now access your requested files.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await message.reply_text("<b>❌ Invalid or Expired Token!</b>\n\nPlease try generating a new token.", parse_mode=ParseMode.HTML)
            return

        # --- 2. Check Verification for File Access ---
        if IS_VERIFY and (user_id not in ADMINS) and (SHORTLINK_URL and SHORTLINK_API):
            if not await is_user_verified(user_id):
                chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                random_token = ''.join(random.choices(chars, k=10))
                await update_verify_status(user_id, random_token)
                
                verification_url = f"https://t.me/{client.username}?start=verify_{random_token}"
                shortened_url = await get_shortlink(verification_url)
                
                verify_buttons = [
                    [InlineKeyboardButton("🔓 Verify Token (Click Here)", url=shortened_url)],
                    [InlineKeyboardButton("Tutorial (How To Verify)", url=VERIFY_TUTORIAL)]
                ]
                await message.reply_text(
                    f"<b>⚠️ Access Denied! Verification Required.</b>\n\n"
                    f"You must verify your token to download this file.\n"
                    f"Click on <b>'Verify Token'</b> below to get access (Valid for <b>{verify_expire_time}</b>).",
                    reply_markup=InlineKeyboardMarkup(verify_buttons),
                    parse_mode=ParseMode.HTML,
                    protect_content=True
                )
                return

        # --- 3. File Retrieval ---
        decoded_string = await decode(base64_string)
        argument = decoded_string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        else:
            return

        temp_msg = await message.reply("Please Wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something Went Wrong..!")
            return
        await temp_msg.delete()

        madflix_msgs = []

        for msg in messages:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                madflix_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                madflix_msgs.append(madflix_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                madflix_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT
                )
                madflix_msgs.append(madflix_msg)
            except:
                pass

        k = await client.send_message(
            chat_id=message.from_user.id,
            text=f"<b>❗️ <u>IMPORTANT</u> ❗️</b>\n\nThis Video / File Will Be Deleted In {file_auto_delete} (Due To Copyright Issues).\n\n📌 Please Forward This Video / File To Somewhere Else And Start Downloading There.",
            parse_mode=ParseMode.HTML
        )

        asyncio.create_task(delete_files(madflix_msgs, client, k))
        return

    await send_styled_start(client, message)


@Bot.on_message(filters.command('start') & filters.private & ~subscribed)
async def not_joined(client: Client, message: Message):
    await send_styled_start(client, message)


# --- Callback Handler with 100% Reliable Matching Filter ---
check_filter = filters.create(lambda _, __, query: query.data == "check_verification")

@Bot.on_callback_query(check_filter)
async def check_verification_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id

    try:
        # Shobar aage loader dismiss kora
        await query.answer()

        # 1. Force Subscription check
        sub_status = await is_subscribed(None, client, query)
        if not sub_status:
            await client.send_message(
                chat_id=user_id,
                text="<b>❌ You haven't joined all required channels yet!</b>\n\nPlease join all channels shown above and tap <b>'Try Again / Verify'</b> again.",
                parse_mode=ParseMode.HTML
            )
            return

        # 2. Token verification check
        if IS_VERIFY and (user_id not in ADMINS) and (SHORTLINK_URL and SHORTLINK_API):
            if await is_user_verified(user_id):
                await client.send_message(
                    chat_id=user_id,
                    text=f"<b>✅ You are already verified!</b>\n\nYou have unrestricted access for <b>{verify_expire_time}</b>. Enjoy downloading your files!",
                    parse_mode=ParseMode.HTML
                )
                return
            else:
                chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                random_token = ''.join(random.choices(chars, k=10))
                await update_verify_status(user_id, random_token)
                
                verification_url = f"https://t.me/{client.username}?start=verify_{random_token}"
                shortened_url = await get_shortlink(verification_url)
                
                verify_buttons = [
                    [InlineKeyboardButton("🔓 Verify Token (Click Here)", url=shortened_url)],
                    [InlineKeyboardButton("Tutorial (How To Verify)", url=VERIFY_TUTORIAL)]
                ]
                await client.send_message(
                    chat_id=user_id,
                    text=(
                        f"<b>⚠️ Access Denied! Verification Required.</b>\n\n"
                        f"You must complete token verification to use this bot.\n\n"
                        f"Click on <b>'Verify Token'</b> below to get access (Valid for <b>{verify_expire_time}</b>)."
                    ),
                    reply_markup=InlineKeyboardMarkup(verify_buttons),
                    parse_mode=ParseMode.HTML,
                    protect_content=True
                )
                return
        else:
            await client.send_message(
                chat_id=user_id,
                text="<b>✅ You are verified!</b>\n\nYou have full access to this bot.",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        print(f"Error in check_verification callback: {e}")
        try:
            await client.send_message(
                chat_id=user_id,
                text="<b>⚠️ Something went wrong!</b> Please send /start again.",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass


@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="Processing...")
    users = await full_userbase()
    await msg.edit(f"{len(users)} Users Are Using This Bot")


@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1

        status = f"""<b><u>Broadcast Completed</u></b>

<b>Total Users :</b> <code>{total}</code>
<b>Successful :</b> <code>{successful}</code>
<b>Blocked Users :</b> <code>{blocked}</code>
<b>Deleted Accounts :</b> <code>{deleted}</code>
<b>Unsuccessful :</b> <code>{unsuccessful}</code>"""

        return await pls_wait.edit(status)

    else:
        msg = await message.reply("Use This Command As A Reply To Any Telegram Message With Out Any Spaces.")
        await asyncio.sleep(8)
        await msg.delete()


async def delete_files(messages, client, k):
    await asyncio.sleep(FILE_AUTO_DELETE)
    for msg in messages:
        try:
            await client.delete_messages(chat_id=msg.chat.id, message_ids=[msg.id])
        except Exception as e:
            print(f"The attempt to delete the media {msg.id} was unsuccessful: {e}")
    await k.edit_text("Your Video / File Is Successfully Deleted ✅")
