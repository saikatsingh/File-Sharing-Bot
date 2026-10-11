from aiohttp import web
from plugins import web_server
import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from config import API_HASH, API_ID, LOGGER, BOT_TOKEN, TG_BOT_WORKERS, FORCE_SUB_CHANNEL, CHANNEL_ID, PORT
import pyrogram.utils

# টেলিগ্রামের দীর্ঘ চ্যানেল আইডির জন্য নিরাপদ রেঞ্জ
pyrogram.utils.MIN_CHANNEL_ID = -100999999999999


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # ফোর্স সাব চ্যানেল যাচাই
        if FORCE_SUB_CHANNEL:
            try:
                chat = await self.get_chat(FORCE_SUB_CHANNEL)
                link = chat.invite_link
                if not link:
                    link = await self.export_chat_invite_link(FORCE_SUB_CHANNEL)
                self.invitelink = link
            except Exception as a:
                self.LOGGER(__name__).warning(f"Error getting invite link from FORCE_SUB_CHANNEL: {a}")
                self.LOGGER(__name__).warning("Make sure the Bot is Admin in Force Sub Channel with invite permissions!")

        # ডাটাবেজ চ্যানেল যাচাই
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Hey 🖐")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            self.LOGGER(__name__).warning(f"Make sure Bot is Admin in DB Channel, Current CHANNEL_ID: {CHANNEL_ID}")
            self.LOGGER(__name__).info("\nBot Stopped. Join support group for help.")
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running...!")
        self.LOGGER(__name__).info("ミ💖 MADFLIX BOTZ 💖彡")
        self.username = usr_bot_me.username

        # কয়ব হেলথ চেকের জন্য ওয়েব সার্ভার
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            bind_address = "0.0.0.0"
            server_port = int(PORT) if str(PORT).isdigit() else 8080
            await web.TCPSite(app, bind_address, server_port).start()
        except Exception as err:
            self.LOGGER(__name__).warning(f"Web server failed to start: {err}")

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot Stopped...")
