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

# 2. Main / Public Channels (Jekhane apni post korben; space diye multiple channel ID dite parben)
MAIN_CHANNEL_IDS = [
    int(x) for x in os.environ.get("MAIN_CHANNEL_IDS", "-1004420561870").split() if x
]

# Purono code er compatibility er jonno single ID fallback
MAIN_CHANNEL_ID = MAIN_CHANNEL_IDS[0] if MAIN_CHANNEL_IDS else int(os.environ.get("MAIN_CHANNEL_ID", "-1004420561870"))

# FORCE_SUB_CHANNELS e space diye multiple channel ID dite parben
FORCE_SUB_CHANNELS = [
    int(x) for x in os.environ.get("FORCE_SUB_CHANNELS", "-1004396186497 -1004420561870 -1004316896651").split() if x
]

FORCE_SUB_CHANNEL = FORCE_SUB_CHANNELS[0] if FORCE_SUB_CHANNELS else None
FILE_AUTO_DELETE = int(os.getenv("FILE_AUTO_DELETE", "600"))

PORT = os.environ.get("PORT", "8080")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

# --- Direct Telegraph / Graph.org Image Links ---
START_PICS = os.environ.get(
    "START_PICS", 
    "https://graph.org/file/d3f66c0cb2cd8664af575-e6dd7eeebcd3fdd005.jpg https://graph.org/file/e2a33b8b2ae45c9594506-c43f4ada14b15dabdc.jpg https://graph.org/file/7f28ec9ced2dd01bebee6-b5c4e476b2bd69c331.jpg https://graph.org/file/07dc69570c16d91faa8c0-c7c741bee49e0a3b02.jpg https://graph.org/file/9d15b6eeab8b472023ecf-dc445d4892c5240e00.jpg https://graph.org/file/92ee3750b2232f9a9368e-7706fa291d3cf4b6f0.jpg https://graph.org/file/ba40a70e4b7103bfa9e2b-2fed918681a195fd8f.jpg https://graph.org/file/058c90f75ddb177bfb3bb-881bbf3bfccf734d6b.jpg https://graph.org/file/e4f279d55501def43a588-c88376c0b53dcfba52.jpg https://graph.org/file/da663888ee8ab9dffdbaf-c7a0ee60b32a903d1d.jpg https://graph.org/file/71d9775c4afb502753a83-215e762ff7eb5e5e25.jpg https://graph.org/file/87ba281d4ed36a2f89ff5-7ee8642facd21e6641.jpg https://graph.org/file/db03a4c74ef3caec3dc35-a8c466979d0addf768.jpg https://graph.org/file/a95671433db3cf9d31f07-23267bef65128408ce.jpg https://graph.org/file/8d2e76ec4437df2da0da1-f954c181a644e0b123.jpg https://graph.org/file/8ef2eff157a3f2b9a7956-5105e5eace6e1c86e5.jpg https://graph.org/file/276b5b2ff60ec9f12c00f-134a6b312d9c7d27cf.jpg https://graph.org/file/fea700ef9fe426d1827b2-e5b17cd73aab4a86f0.jpg https://graph.org/file/a0816c2bcdf901c39cb0e-9424e78becdd4a14e9.jpg https://graph.org/file/43106eab942f21491840f-078784e74986872d50.jpg https://graph.org/file/a79a1a4d828eda1e611b7-4bb3dcc23f0674fe38.jpg https://graph.org/file/ed61bcaa0625b167e1174-1985f766823c976356.jpg https://graph.org/file/4b6dac0d06cffc0f35614-03b268efcb9f4dc931.jpg https://graph.org/file/68c207c5c4ba66c06f02b-ec50a2b1c1bb901a4b.jpg https://graph.org/file/7f8f1954c1e9c2eeb6aef-b0538de0c53f5e5ecf.jpg https://graph.org/file/742e29a4523d06663e9c5-cdd0db51a6c51842ca.jpg https://graph.org/file/94467539277ee064d0dba-1fba06c0f5e4955c2e.jpg https://graph.org/file/ac04db422015dccc67cdf-ebcff78fc51349316d.jpg https://graph.org/file/93c5a96b834d7de7152e8-901adac23df2a8e725.jpg https://graph.org/file/c2091215ac8cf4e92a255-72be9a237587f582cd.jpg https://graph.org/file/0ffcff439898f9283f1a2-184c295e74974fce51.jpg https://graph.org/file/f287c4ae7440015ef2fa0-6065639c193780344c.jpg https://graph.org/file/4abe9a7eb2bee26e8e32b-f261a9b120e2bb640b.jpg https://graph.org/file/2c67b5e37076f03bb354c-710cb494ca3d15f6d7.jpg https://graph.org/file/805de7c2c5d757b5c576d-c4fa7629f0fa182f8f.jpg https://graph.org/file/a9d6e018a6785bea41afd-e2e1be3e17ee3f0197.jpg https://graph.org/file/79ef6412b935aacc49521-69a29bd0f01c55edba.jpg https://graph.org/file/c2b30105e2d6c2e1a8496-4750e51ab3440e669b.jpg https://graph.org/file/28fd8f04ff34b7fe2c12a-d1224d1e89117da61d.jpg https://graph.org/file/31f362dfd548eb6a29b05-006356e75c186826a1.jpg https://graph.org/file/8728e70b605dd4568cfb9-1007b9fe91cd5c5ac8.jpg https://graph.org/file/1157e8d3f31c1813af75a-be71213bcab00292f4.jpg https://graph.org/file/11adfa3437c0c894da6a6-5be9fd535d4ae9529b.jpg https://graph.org/file/fc6608a09020b7a504793-5eeffbde3206669b9f.jpg https://graph.org/file/dec1784641e71d101c74c-135e1135eaa7f1d651.jpg https://graph.org/file/e9da75ae534b846bc2643-1181152b9ddbbfd6b3.jpg https://graph.org/file/f23b4c2ec1abf0f450cc5-606180501048be8468.jpg"
).split()

# --- Token Verification & Shortener Settings ---
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "arolinks.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "a769587e8ee75b1cec273858ff616230b9b8d912")
IS_VERIFY = True if os.environ.get("IS_VERIFY", "True").lower() == "true" else False
VERIFY_EXPIRE = int(os.environ.get("VERIFY_EXPIRE", "28800"))  # 8 hours = 28800 seconds
VERIFY_TUTORIAL = os.environ.get("VERIFY_TUTORIAL", "https://t.me/How_to_open_file_to_link")

# --- Premium / Indian UPI Payment Settings ---
UPI_ID = os.environ.get("UPI_ID", "mailmetosaikat676@okhdfcbank")
UPI_QR_URL = os.environ.get("UPI_QR_URL", "https://graph.org/file/e5ec2cecc24ce6c1dbccf-9bb7df8e3e0d62d6d2.jpg")

PREMIUM_PLANS_TEXT = os.environ.get(
    "PREMIUM_PLANS_TEXT",
    """✦ <b>PREMIUM PLANS:</b> ❞
━━━━━━━━━━━━━━━━━━━━
<b>PERKS:</b>
❒ UNLIMITED DAILY LINKS
❒ FREE LINK BYPASS
❒ PROTECT-CONTENT BYPASS
━━━━━━━━━━━━━━━━━━━━
<b>AVAILABLE PLANS:</b>

›› <b>1 Day :</b> ₹19
›› <b>7 Days :</b> ₹68
›› <b>30 Days :</b> ₹169
›› <b>3 Months :</b> ₹299
›› <b>1 Year :</b> ₹599

✦ <b>AFTER PAYMENT:</b> ❞
Send your 12-digit UPI UTR / Transaction ID for instant activation!"""
)

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

🥵🥵Join Below Channels And Tap Try Again To Continue 🍑🍑"""

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
