import time
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from bot import Bot
from config import ADMINS, UPI_ID, UPI_QR_URL, PREMIUM_PLANS_TEXT
from database.database import is_premium_user, add_premium, remove_premium, get_premium_status

AWAITING_UTR = {}

PLANS_CONFIG = {
    "1": {"days": 1, "price": 19, "name": "1 Day"},
    "7": {"days": 7, "price": 68, "name": "7 Days"},
    "30": {"days": 30, "price": 169, "name": "30 Days"},
    "90": {"days": 90, "price": 299, "name": "3 Months"},
    "365": {"days": 365, "price": 599, "name": "1 Year"}
}

def get_plans_buttons():
    buttons = [
        [
            InlineKeyboardButton("1 DAY", callback_data="buy_plan_1"),
            InlineKeyboardButton("7 DAYS", callback_data="buy_plan_7")
        ],
        [
            InlineKeyboardButton("30 DAYS", callback_data="buy_plan_30"),
            InlineKeyboardButton("3 MONTHS", callback_data="buy_plan_90")
        ],
        [
            InlineKeyboardButton("1 YEAR", callback_data="buy_plan_365")
        ],
        [
            InlineKeyboardButton("‹ Back", callback_data="back_to_premium_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


async def safe_edit(message: Message, text: str, markup: InlineKeyboardMarkup):
    """Photo message hole edit_caption korbe, normal message hole edit_text korbe"""
    try:
        if message.photo:
            await message.edit_caption(caption=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except MessageNotModified:
        pass
    except Exception as e:
        print(f"Error in safe_edit: {e}")


# --- /myplan command ---
@Bot.on_message(filters.command(['myplan']) & filters.private)
async def myplan_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if await is_premium_user(user_id):
        status = await get_premium_status(user_id)
        await message.reply_text(
            f"<b>👑 Premium Status: Active</b>\n\n"
            f"⏳ <b>Remaining Validity:</b> <code>{status}</code>\n"
            f"⚡ Direct instant downloads enabled without ads!",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            "<b>❌ You are currently on Free Plan.</b>\n\nUse /plans to upgrade to Premium!",
            parse_mode=ParseMode.HTML
        )


# --- Start menu theke '⭐ PREMIUM' tap korle ba /plans dile ---
@Bot.on_callback_query(filters.regex('^open_premium_menu$'))
@Bot.on_message(filters.command(['plans', 'buy', 'premium']) & filters.private)
async def premium_intro(client: Client, update):
    is_callback = isinstance(update, CallbackQuery)
    user = update.from_user
    user_id = user.id
    
    if await is_premium_user(user_id):
        status = await get_premium_status(user_id)
        text = f"<b>✅ You are already a Premium Member!</b>\n\n⏳ Validity: <b>{status}</b>"
        if is_callback:
            await update.answer(text, show_alert=True)
        else:
            await update.reply_text(text, parse_mode=ParseMode.HTML)
        return

    text = f"""👋 <b>Hello {user.first_name}</b>

🎖 <b>Want Premium?</b>

› Choose a method below:

╭ <b>💳 Pay with UPI (Instant activation)</b> ❞"""

    buttons = [
        [InlineKeyboardButton("💳 Pay with UPI", callback_data="view_upi_plans")],
        [InlineKeyboardButton("🔒 Close", callback_data="close_message")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    if is_callback:
        await update.answer()
        await safe_edit(update.message, text, markup)
    else:
        await update.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@Bot.on_callback_query(filters.regex('^back_to_premium_home$'))
async def back_to_premium_home_cb(client: Client, query: CallbackQuery):
    await query.answer()
    text = f"""👋 <b>Hello {query.from_user.first_name}</b>

🎖 <b>Want Premium?</b>

› Choose a method below:

╭ <b>💳 Pay with UPI (Instant activation)</b> ❞"""

    buttons = [
        [InlineKeyboardButton("💳 Pay with UPI", callback_data="view_upi_plans")],
        [InlineKeyboardButton("🔒 Close", callback_data="close_message")]
    ]
    await safe_edit(query.message, text, InlineKeyboardMarkup(buttons))


# --- '💳 Pay with UPI' tap korle plans list show kora ---
@Bot.on_callback_query(filters.regex('^view_upi_plans$'))
async def view_plans_cb(client: Client, query: CallbackQuery):
    await query.answer()
    await safe_edit(query.message, PREMIUM_PLANS_TEXT, get_plans_buttons())


# --- Plan Select Korle QR Code + UTR Details ---
@Bot.on_callback_query(filters.regex('^buy_plan_'))
async def plan_selected_cb(client: Client, query: CallbackQuery):
    await query.answer()
    plan_key = query.data.split('_')[2]
    plan = PLANS_CONFIG.get(plan_key, PLANS_CONFIG["30"])
    user_id = query.from_user.id
    AWAITING_UTR[user_id] = plan["days"]

    trx_id = f"TRX{int(time.time())}{user_id % 10000}"

    caption = f"""✦ <b>PREMIUM PAYMENT</b> ❞
━━━━━━━━━━━━━━━━━━━━
❒ <b>Amount:</b> ₹{plan['price']}
≡ <b>VALIDITY:</b> {plan['name']}
❒ <b>TRANSACTION ID:</b> <code>{trx_id}</code>
━━━━━━━━━━━━━━━━━━━━
≡ <b>SCAN THIS QR WITH ANY UPI APP TO PAY.</b>

✦ <b>UPI ID:</b> <code>{UPI_ID}</code>

✦ <b>PREMIUM WILL BE ADDED AUTOMATICALLY:</b>
After payment, send your <b>12-digit UTR number</b> here!"""

    buttons = [
        [InlineKeyboardButton("❌ CANCEL", callback_data="back_to_premium_home")]
    ]

    try:
        await query.message.delete()
    except Exception:
        pass

    if UPI_QR_URL and UPI_QR_URL.startswith("http"):
        try:
            await client.send_photo(
                chat_id=user_id,
                photo=UPI_QR_URL,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            print(f"QR photo error: {e}")

    await client.send_message(chat_id=user_id, text=caption, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


# --- UTR input dhora (Auto Alert to Admin) ---
@Bot.on_message(filters.private & filters.text & ~filters.command(['start', 'plans', 'buy', 'premium', 'myplan', 'broadcast', 'users', 'add_premium', 'remove_premium']))
async def utr_listener(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in AWAITING_UTR:
        return

    utr_text = message.text.strip()
    if not (utr_text.isdigit() and len(utr_text) == 12):
        await message.reply_text(
            "<b>❌ Invalid UTR Number!</b>\n\nPlease send the exact <b>12-digit</b> UPI Transaction / UTR ID from your payment receipt.",
            parse_mode=ParseMode.HTML
        )
        return

    plan_days = AWAITING_UTR.pop(user_id)
    plan_name = f"{plan_days} Days" if plan_days != 365 else "1 Year"

    await message.reply_text(
        "<b>⏳ UTR Received!</b>\n\nYour payment is being verified by Admin. You will receive an instant notification once approved.",
        parse_mode=ParseMode.HTML
    )

    admin_buttons = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{user_id}_{plan_days}_{utr_text}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{user_id}_{utr_text}")
        ]
    ]

    admin_msg = f"""<b>🔔 New Premium Payment Alert!</b>

👤 <b>User:</b> {message.from_user.mention} (<code>{user_id}</code>)
📦 <b>Plan:</b> {plan_name}
🔢 <b>UTR / Ref ID:</b> <code>{utr_text}</code>

<i>Verify on your UPI app and tap below:</i>"""

    for admin_id in ADMINS:
        try:
            await client.send_message(
                chat_id=admin_id,
                text=admin_msg,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error alerting admin {admin_id}: {e}")


# --- 1-Click Auto Approval Callback ---
@Bot.on_callback_query(filters.regex('^adm_app_'))
async def approve_cb(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        await query.answer("Access Denied!", show_alert=True)
        return

    data = query.data.split('_')
    target_user_id = int(data[2])
    plan_days = int(data[3])
    utr_text = data[4]

    await add_premium(target_user_id, plan_days)
    plan_name = f"{plan_days} Days" if plan_days != 365 else "1 Year"

    await query.message.edit_text(f"{query.message.text}\n\n<b>✅ APPROVED by {query.from_user.mention}</b>", parse_mode=ParseMode.HTML)
    await query.answer("Premium Activated!", show_alert=True)

    try:
        await client.send_message(
            chat_id=target_user_id,
            text=f"<b>🎉 Payment Approved!</b>\n\nYour <b>{plan_name}</b> premium subscription is now active! Enjoy unlimited downloads without any ads.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Error messaging user: {e}")


# --- 1-Click Auto Reject Callback ---
@Bot.on_callback_query(filters.regex('^adm_rej_'))
async def reject_cb(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        await query.answer("Access Denied!", show_alert=True)
        return

    data = query.data.split('_')
    target_user_id = int(data[2])
    utr_text = data[3]

    await query.message.edit_text(f"{query.message.text}\n\n<b>❌ REJECTED by {query.from_user.mention}</b>", parse_mode=ParseMode.HTML)
    await query.answer("Payment Rejected!", show_alert=True)

    try:
        await client.send_message(
            chat_id=target_user_id,
            text=f"<b>❌ Verification Failed!</b>\n\nYour UTR <code>{utr_text}</code> was rejected by Admin. Please check your payment and retry.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Error messaging user: {e}")


# --- Manual Admin Commands to Directly Add/Remove Premium ---
@Bot.on_message(filters.command('add_premium') & filters.private & filters.user(ADMINS))
async def manual_add_premium(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply_text(
            "<b>⚠️ Usage Format:</b>\n<code>/add_premium [User_ID] [Days]</code>\n\n<b>Example:</b>\n<code>/add_premium 123456789 30</code>",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        target_id = int(message.command[1])
        days = int(message.command[2])
    except ValueError:
        await message.reply_text("<b>❌ User ID and Days must be valid numbers!</b>", parse_mode=ParseMode.HTML)
        return

    await add_premium(target_id, days)
    plan_name = f"{days} Days" if days != 365 else "1 Year"

    await message.reply_text(
        f"<b>✅ Successfully added Premium!</b>\n\n"
        f"👤 <b>User ID:</b> <code>{target_id}</code>\n"
        f"⏳ <b>Validity:</b> <b>{plan_name}</b>",
        parse_mode=ParseMode.HTML
    )

    try:
        await client.send_message(
            chat_id=target_id,
            text=f"<b>🎉 You have been gifted Premium Membership!</b>\n\n"
                 f"Validity: <b>{plan_name}</b>\n"
                 f"Enjoy unlimited direct file downloads without any link bypass or ads.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Could not notify user {target_id}: {e}")


@Bot.on_message(filters.command('remove_premium') & filters.private & filters.user(ADMINS))
async def manual_remove_premium(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "<b>⚠️ Usage Format:</b>\n<code>/remove_premium [User_ID]</code>\n\n<b>Example:</b>\n<code>/remove_premium 123456789</code>",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        target_id = int(message.command[1])
    except ValueError:
        await message.reply_text("<b>❌ User ID must be a valid number!</b>", parse_mode=ParseMode.HTML)
        return

    await remove_premium(target_id)

    await message.reply_text(
        f"<b>✅ Premium removed for User:</b> <code>{target_id}</code>",
        parse_mode=ParseMode.HTML
    )

    try:
        await client.send_message(
            chat_id=target_id,
            text="<b>⚠️ Your Premium access has been removed or revoked by Admin.</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Could not notify user {target_id}: {e}")
