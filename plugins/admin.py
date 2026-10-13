import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from bot import Bot
from config import ADMINS
from database.database import (
    full_userbase, del_user, ban_user, unban_user, 
    is_banned, get_db_stats, clear_database_posts
)


# --- 1. /status COMMAND (Storage, Stats & Users Info) ---
@Bot.on_message(filters.command('status') & filters.private & filters.user(ADMINS))
async def bot_status(client: Client, message: Message):
    msg = await message.reply_text("📊 <i>Fetching Database Statistics...</i>")
    stats = await get_db_stats()
    
    status_text = f"""📊 <b><u>BOT & DATABASE STATUS</u></b>

👥 <b>Total Users:</b> <code>{stats['users']}</code>
⭐ <b>Premium Users:</b> <code>{stats['premium']}</code>
🚫 <b>Banned Users:</b> <code>{stats['banned']}</code>
──────────────────────
💾 <b>MongoDB Data Size:</b> <code>{stats['data_size']} MB</code>
📦 <b>Storage Allocated:</b> <code>{stats['storage_size']} MB</code>
🟢 <b>Free Space Available:</b> <code>{stats['free_storage']} MB / 512 MB</code>

⚡ <i>Database Connection: Active & Healthy</i>"""

    await msg.edit_text(status_text)


# --- 2. /cleardb COMMAND (Temporary Token & Daily Cache Purge) ---
@Bot.on_message(filters.command('cleardb') & filters.private & filters.user(ADMINS))
async def cleardb_command(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton("⚠️ Yes, Clear Data", callback_data="confirm_cleardb"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_cleardb")
        ]
    ]
    await message.reply_text(
        "<b>⚠️ WARNING:</b>\n\nApni ki Database theke cached verify tokens ebong daily 1-free usage reset korte chan? (Users account ba premium subscriptions delete hobe na).",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Bot.on_callback_query(filters.regex('^confirm_cleardb$') & filters.user(ADMINS))
async def confirm_cleardb_callback(client: Client, query: CallbackQuery):
    await query.answer("Clearing...", show_alert=False)
    count = await clear_database_posts()
    await query.message.edit_text(f"✅ <b>Database Successfully Cleared!</b>\n\nTotal <code>{count}</code> user record cache reset kora hoyeche.")


@Bot.on_callback_query(filters.regex('^cancel_cleardb$') & filters.user(ADMINS))
async def cancel_cleardb_callback(client: Client, query: CallbackQuery):
    await query.answer("Cancelled!")
    await query.message.edit_text("❌ Database cleanup process cancelled.")


# --- 3. /ban USER COMMAND ---
@Bot.on_message(filters.command('ban') & filters.private & filters.user(ADMINS))
async def ban_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("<b>Format:</b> <code>/ban [User_ID]</code>")

    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Valid numeric User ID din.")

    if target_id in ADMINS:
        return await message.reply_text("❌ Admin-ke ban kora jabe na.")

    await ban_user(target_id)
    await message.reply_text(f"🚫 User <code>{target_id}</code>-ke ban kora hoyeche.")
    
    try:
        await client.send_message(
            chat_id=target_id, 
            text="<b>⚠️ You have been banned from using this bot!</b>"
        )
    except Exception:
        pass


# --- 4. /unban USER COMMAND ---
@Bot.on_message(filters.command('unban') & filters.private & filters.user(ADMINS))
async def unban_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("<b>Format:</b> <code>/unban [User_ID]</code>")

    try:
        target_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("❌ Valid numeric User ID din.")

    await unban_user(target_id)
    await message.reply_text(f"✅ User <code>{target_id}</code>-ke unban kora hoyeche.")
    
    try:
        await client.send_message(
            chat_id=target_id, 
            text="<b>🎉 You have been unbanned! You can now access the bot again.</b>"
        )
    except Exception:
        pass


# --- 5. /broadcast COMMAND ---
@Bot.on_message(filters.command('broadcast') & filters.private & filters.user(ADMINS))
async def broadcast_command(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Kono text, photo ba media message-e Reply kore <code>/broadcast</code> likhun.")

    users = await full_userbase()
    b_msg = message.reply_to_message
    total = len(users)
    successful = 0
    blocked = 0
    deleted = 0
    failed = 0

    pls = await message.reply_text(f"🚀 <i>Broadcasting to {total} users...</i>")

    for user_id in users:
        try:
            await b_msg.copy(chat_id=user_id)
            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await b_msg.copy(chat_id=user_id)
            successful += 1
        except UserIsBlocked:
            await del_user(user_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(user_id)
            deleted += 1
        except Exception:
            failed += 1

    await pls.edit_text(f"""📢 <b><u>Broadcast Completed</u></b>

👥 <b>Total Users:</b> <code>{total}</code>
✅ <b>Successful:</b> <code>{successful}</code>
🚫 <b>Blocked:</b> <code>{blocked}</code>
🗑 <b>Deleted Accounts:</b> <code>{deleted}</code>
⚠️ <b>Failed:</b> <code>{failed}</code>""")
