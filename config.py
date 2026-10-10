import os
import logging
from logging.handlers import RotatingFileHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "22244082"))
API_HASH = os.environ.get("API_HASH", "fc90b0390b0130286c2676a19ed9c4da")

OWNER_ID = int(os.environ.get("OWNER_ID", "6917766710"))
DB_URL = os.environ.get("DB_URL", "mongodb+srv://creazyhub973_db_user:oMUkVmwbroxS4wZI@cluster0.roacxws.mongodb.net/?appName=Cluster0&compressors=zlib")
DB_NAME = os.environ.get("DB_NAME", "madflixbotz")

# Main / Public Channel (যেখানে আপনি ভিডিও দেবেন, যা পরে ফটো ও বাটনে বদলে যাবে)
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004420561870"))

# Private Database Channel (যেখানে মূল ফাইল/ভিডিও সেভ থাকবে)
DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "-1004345291636"))
# FORCE_SUB_CHANNELS e space diye multiple channel id dite parben (e.g. "-100123456789 -100987654321")
FORCE_SUB_CHANNELS = [
    int(x) for x in os.environ.get("FORCE_SUB_CHANNELS", "-1004396186497 -1002666935141").split() if x
]

# bot.py jate crash na kore tar jonno first channel-ti FORCE_SUB_CHANNEL hishebe rakha holo
FORCE_SUB_CHANNEL = FORCE_SUB_CHANNELS[0] if FORCE_SUB_CHANNELS else None
FILE_AUTO_DELETE = int(os.getenv("FILE_AUTO_DELETE", "600")) # auto delete in seconds

PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# --- Token Verification & Shortener Settings ---
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "nowshort.com") # e.g. "droplink.co" or "gplinks.com" (without https://)
SHORTLINK_API = os.environ.get("SHORTLINK_API", "78985d959bb9aac8ed8d2989973cbef110ed00c4") # Your Shortener API Key
IS_VERIFY = True if os.environ.get("IS_VERIFY", "True").lower() == "true" else False
VERIFY_EXPIRE = int(os.environ.get("VERIFY_EXPIRE", "86400")) # 86400 seconds = 24 hours
VERIFY_TUTORIAL = os.environ.get("VERIFY_TUTORIAL", "https://t.me/How_to_open_file_to_link") # Tutorial video or guide link

try:
    ADMINS = [6917766710]
    for x in (os.environ.get("ADMINS", "6917766710").split()):
        ADMINS.append(int(x))
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False
DISABLE_CHANNEL_BUTTON = True if os.environ.get('DISABLE_CHANNEL_BUTTON', "False") == "True" else False
BOT_STATS_TEXT = "<b>BOT UPTIME :</b>\n{uptime}"

USER_REPLY_TEXT = "❌ Don't Send Me Messages Directly I'm Only File Share Bot !"
START_MSG = os.environ.get("START_MESSAGE", "Hello {mention}\n\nI Can Store Private Files In Specified Channel And Other Users Can Access It From Special Link.")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "Hello {mention}\n\n<b>You Need To Join In My Channel/Group To Use Me\n\nKindly Please Join Channel</b>")

ADMINS.append(OWNER_ID)
ADMINS.append(6917766710)
ADMINS = list(set(ADMINS))

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
