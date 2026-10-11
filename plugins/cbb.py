from pyrogram import __version__
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
from bot import Bot
from config import OWNER_ID, PREMIUM_PLANS_TEXT
from database.database import is_premium_user, get_premium_status

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


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user = query.from_user
    user_id = user.id

    # 1. Purono About Handler
    if data == "about":
        await query.answer()
        await query.message.edit_text(
            text=f"<b>🤖 My Name :</b> <a href='https://t.me/Cron_House_Bot'>File Sharing Bot</a> \n<b>📝 Language :</b> <a href='https://python.org'>Python 3</a> \n<b>📚 Library :</b> <a href='https://pyrogram.org'>Pyrogram {__version__}</a> \n<b>🚀 Server :</b> <a href='https://heroku.com'>Heroku</a> \n<b>📢 Channel :</b> <a href='https://t.me/Leazy_support_group'>Madflix Botz</a> \n<b>🧑‍💻 Developer :</b> <a href='tg://user?id={OWNER_ID}'>Jishu Developer</a>",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔒 Close", callback_data="close")
                    ]
                ]
            )
        )
        return

    # 2. Close Handler (duto key-i cover kora holo)
    elif data in ["close", "close_message"]:
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        try:
            await query.message.reply_to_message.delete()
        except Exception:
            pass
        return

    # 3. Premium Menu Handler
    elif data == "open_premium_menu":
        await query.answer()
        if await is_premium_user(user_id):
            status = await get_premium_status(user_id)
            await query.answer(f"✅ You are already Premium!\nValidity: {status}", show_alert=True)
            return

        text = f"""👋 <b>Hello {user.first_name}</b>\n\n🎖 <b>Want Premium?</b>\n\n› Choose a method below:\n\n╭ <b>💳 Pay with UPI (Instant activation)</b> ❞"""
        buttons = [
            [InlineKeyboardButton("💳 Pay with UPI", callback_data="view_upi_plans")],
            [InlineKeyboardButton("🔒 Close", callback_data="close")]
        ]
        
        await client.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return

    # 4. Help Menu Handler
    elif data == "open_help_menu":
        await query.answer()
        help_text = """○ <b>OWNER :</b> Admin

📝 <b>Basic Users Commands:</b>

• /start - Start the bot
• /help - Open help menu
• /myplan - Check premium status

💡 <b>Tip:</b> Use /myplan to see your subscription details!

╭ <b>File Access:</b> ❞
• Click on any file link to access shared content.
• Premium users get unlimited access!!"""

        buttons = [
            [
                InlineKeyboardButton("⬅️ BACK", callback_data="back_to_start_home"),
                InlineKeyboardButton("CLOSE ❌", callback_data="close")
            ]
        ]

        try:
            if query.message.photo:
                await query.message.edit_caption(
                    caption=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.message.edit_text(
                    text=help_text,
                    reply_markup=InlineKeyboardMarkup(buttons),
                    parse_mode=ParseMode.HTML
                )
        except MessageNotModified:
            pass
        except Exception:
            await client.send_message(
                chat_id=user_id,
                text=help_text,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.HTML
            )
        return

    # 5. Pay with UPI (View Plans)
    elif data == "view_upi_plans":
        await query.answer()
        try:
            await query.message.edit_text(
                PREMIUM_PLANS_TEXT,
                reply_markup=get_plans_buttons(),
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await client.send_message(
                chat_id=user_id,
                text=PREMIUM_PLANS_TEXT,
                reply_markup=get_plans_buttons(),
                parse_mode=ParseMode.HTML
            )
        return

    # 6. Back to Premium Home
    elif data == "back_to_premium_home":
        await query.answer()
        text = f"""👋 <b>Hello {user.first_name}</b>\n\n🎖 <b>Want Premium?</b>\n\n› Choose a method below:\n\n╭ <b>💳 Pay with UPI (Instant activation)</b> ❞"""
        buttons = [
            [InlineKeyboardButton("💳 Pay with UPI", callback_data="view_upi_plans")],
            [InlineKeyboardButton("🔒 Close", callback_data="close")]
        ]
        try:
            await query.message.delete()
        except Exception:
            pass
        await client.send_message(
            chat_id=user_id, 
            text=text, 
            reply_markup=InlineKeyboardMarkup(buttons), 
            parse_mode=ParseMode.HTML
        )
        return

    # 7. Baki onno callback thakle (jemon start.py ba premium.py er handlers) shegulate event pass kore dewa
    else:
        await query.continue_propagation()
