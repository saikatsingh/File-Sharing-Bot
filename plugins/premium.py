from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from config import ADMINS, UPI_ID, UPI_QR_URL, PREMIUM_PLANS_TEXT
from database.database import is_premium_user, add_premium, get_premium_status

# User jokhon plan select korbe, tar ID ebong plan track korar jonno
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
        ]
    ]
    return InlineKeyboardMarkup(buttons)


# --- /plans ba /premium command handler ---
@Bot.on_message(filters.command(['plans', 'buy', 'premium']) & filters.private)
async def plans_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # User jodi already premium thake
    if await is_premium_user(user_id):
        status = await get_premium_status(user_id)
        await message.reply_text(
            f"<b>✅ You are already a Premium Member!</b>\n\n"
            f"⏳ Remaining Validity: <b>{status}</b>\n"
            f"Enjoy unlimited direct file downloads without any ads.",
            parse_mode=ParseMode.HTML
        )
        return

    await message.reply_text(
        PREMIUM_PLANS_TEXT,
        reply_markup=get_plans_buttons(),
        parse_mode=ParseMode.HTML
    )


# --- Plan Select Callback ---
@Bot.on_callback_query(filters.regex('^buy_plan_'))
async def buy_plan_callback(client: Client, query: CallbackQuery):
    await query.answer()
    plan_key = query.data.split('_')[2]
    plan = PLANS_CONFIG.get(plan_key, PLANS_CONFIG["30"])
    user_id = query.from_user.id

    # Store user state
    AWAITING_UTR[user_id] = plan["days"]

    caption = f"""✦ <b>PAYMENT DETAILS:</b> ❞
━━━━━━━━━━━━━━━━━━━━
<b>Plan:</b> {plan['name']}
<b>Amount:</b> ₹{plan['price']}
<b>UPI ID:</b> <code>{UPI_ID}</code>
━━━━━━━━━━━━━━━━━━━━
<b>INSTRUCTIONS:</b>
1. Scan the QR code or send <b>₹{plan['price']}</b> to the UPI ID.
2. Complete the payment from GPay, PhonePe, or Paytm.
3. Copy the <b>12-digit UTR / Ref Number</b>.
4. <b>Directly send that 12-digit number here in this chat.</b>"""

    buttons = [[InlineKeyboardButton("‹ Back", callback_data="back_to_plans_list")]]

    if UPI_QR_URL and UPI_QR_URL.startswith("http"):
        try:
            await query.message.reply_photo(
                photo=UPI_QR_URL,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
            return
        except Exception as e:
            print(f"Error sending QR code: {e}")

    await query.message.reply_text(
        caption,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )


# --- Back Button Callback ---
@Bot.on_callback_query(filters.regex('^back_to_plans_list$'))
async def back_callback(client: Client, query: CallbackQuery):
    AWAITING_UTR.pop(query.from_user.id, None)
    await query.message.delete()
    await query.message.reply_text(
        PREMIUM_PLANS_TEXT,
        reply_markup=get_plans_buttons(),
        parse_mode=ParseMode.HTML
    )


# --- User 12-Digit UTR Input Handler ---
@Bot.on_message(filters.private & filters.text & ~filters.command(['start', 'plans', 'buy', 'premium', 'broadcast', 'users']))
async def utr_receiver(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in AWAITING_UTR:
        return

    utr_text = message.text.strip()
    
    # Exactly 12-digit numeric check
    if not (utr_text.isdigit() and len(utr_text) == 12):
        await message.reply_text(
            "<b>❌ Invalid UTR Number!</b>\n\n"
            "Please send the valid <b>12-digit</b> UPI Transaction / UTR ID from your payment receipt.",
            parse_mode=ParseMode.HTML
        )
        return

    plan_days = AWAITING_UTR.pop(user_id)
    plan_name = f"{plan_days} Days" if plan_days != 365 else "1 Year"

    await message.reply_text(
        "<b>⏳ UTR Received!</b>\n\n"
        "Your payment verification has been submitted to Admin. "
        "You will receive an instant notification as soon as it gets approved.",
        parse_mode=ParseMode.HTML
    )

    # 1-Click Approve / Reject Buttons for Admin
    admin_buttons = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"adm_app_{user_id}_{plan_days}_{utr_text}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"adm_rej_{user_id}_{utr_text}")
        ]
    ]

    admin_alert_text = f"""<b>🔔 New Premium Payment Alert!</b>

👤 <b>User:</b> {message.from_user.mention} (<code>{user_id}</code>)
📦 <b>Plan:</b> {plan_name}
🔢 <b>UTR / Ref ID:</b> <code>{utr_text}</code>

<i>Please verify the amount in your UPI app and tap below:</i>"""

    for admin_id in ADMINS:
        try:
            await client.send_message(
                chat_id=admin_id,
                text=admin_alert_text,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Failed to alert admin {admin_id}: {e}")


# --- Admin 1-Click Approval Callback ---
@Bot.on_callback_query(filters.regex('^adm_app_'))
async def approve_payment(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        await query.answer("Access Denied!", show_alert=True)
        return

    data = query.data.split('_')
    target_user_id = int(data[2])
    plan_days = int(data[3])
    utr_text = data[4]

    await add_premium(target_user_id, plan_days)
    plan_name = f"{plan_days} Days" if plan_days != 365 else "1 Year"

    await query.message.edit_text(
        f"{query.message.text}\n\n<b>✅ APPROVED by {query.from_user.mention}</b>",
        parse_mode=ParseMode.HTML
    )
    await query.answer("Premium Activated Successfully!", show_alert=True)

    # Notify user
    try:
        await client.send_message(
            chat_id=target_user_id,
            text=(
                f"<b>🎉 Congratulations! Payment Approved.</b>\n\n"
                f"Your <b>{plan_name}</b> premium subscription is now active!\n\n"
                f"✨ <i>All shortlinks and token verifications are now disabled for you. Enjoy direct file access!</i>"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"User message error: {e}")


# --- Admin 1-Click Reject Callback ---
@Bot.on_callback_query(filters.regex('^adm_rej_'))
async def reject_payment(client: Client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        await query.answer("Access Denied!", show_alert=True)
        return

    data = query.data.split('_')
    target_user_id = int(data[2])
    utr_text = data[3]

    await query.message.edit_text(
        f"{query.message.text}\n\n<b>❌ REJECTED by {query.from_user.mention}</b>",
        parse_mode=ParseMode.HTML
    )
    await query.answer("Payment Rejected!", show_alert=True)

    try:
        await client.send_message(
            chat_id=target_user_id,
            text=(
                f"<b>❌ Payment Verification Failed!</b>\n\n"
                f"Your submitted UTR <code>{utr_text}</code> was rejected by Admin.\n"
                f"If you have already paid, please check the transaction details and retry via /plans."
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"User message error: {e}")
