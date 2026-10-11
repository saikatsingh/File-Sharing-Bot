import os
import logging
from logging.handlers import RotatingFileHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", "22244082"))
API_HASH = os.environ.get("API_HASH", "fc90b0390b0130286c2676a19ed9c4da")

OWNER_ID = int(os.environ.get("OWNER_ID", "6917766710"))
DB_URL = os.environ.get("DB_URL", "mongodb+srv://creazyhub973_db_user:oMUkVmwbroxS4wZI@cluster0.roacxws.mongodb.net/?appName=Cluster0&compressors=zlib")
DB_NAME = os.environ.get("DB_NAME", "madflixbotz")

# 1. Database Channel (Private channel, jekhane bot shob original file store korbe)
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004345291636"))

# 2. Main / Public Channel (Jekhane apni video upload korben, ar bot photo+button replace korbe):
MAIN_CHANNEL_ID = int(os.environ.get("MAIN_CHANNEL_ID", "-1004420561870"))

# FORCE_SUB_CHANNELS e space diye multiple channel id dite parben
FORCE_SUB_CHANNELS = [
    int(x) for x in os.environ.get("FORCE_SUB_CHANNELS", "-1004396186497 -1002666935141").split() if x
]

FORCE_SUB_CHANNEL = FORCE_SUB_CHANNELS[0] if FORCE_SUB_CHANNELS else None
FILE_AUTO_DELETE = int(os.getenv("FILE_AUTO_DELETE", "600"))

PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# --- Direct Telegraph / Graph.org Image Links (Space diye apnar link gulo boshabenk) ---
START_PICS = os.environ.get(
    "START_PICS", 
    "https://graph.org/file/56b5deb73f3b132e2bb73.jpg https://graph.org/file/5303692652d91d52180c2.jpg https://graph.org/file/425b6f46efc7c6d64105f.jpg https://graph.org/file/876867e761c6c7a29855b.jpg"
).split()

# --- Token Verification & Shortener Settings ---
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "arolinks.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "a769587e8ee75b1cec273858ff616230b9b8d912")
IS_VERIFY = True if os.environ.get("IS_VERIFY", "True").lower() == "true" else False
VERIFY_EXPIRE = int(os.environ.get("VERIFY_EXPIRE", "28800"))  # 8 hours = 28800 seconds
VERIFY_TUTORIAL = os.environ.get("VERIFY_TUTORIAL", "https://t.me/How_to_open_file_to_link")

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

DEFAULT_WELCOME_TEXT = """Hey {first}
Welcome to @{username}

🥵🥵Join Below Channels And Tap Verify To Continue 🍑🍑"""

START_MSG = os.environ.get("START_MESSAGE", DEFAULT_WELCOME_TEXT)
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", DEFAULT_WELCOME_TEXT)

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
