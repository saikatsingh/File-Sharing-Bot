import pymongo
import time
from config import DB_URL, DB_NAME, VERIFY_EXPIRE

dbclient = pymongo.MongoClient(DB_URL)
database = dbclient[DB_NAME]
user_data = database['users']


async def present_user(user_id: int):
    found = user_data.find_one({'_id': user_id})
    return bool(found)


async def add_user(user_id: int):
    user_data.insert_one({'_id': user_id})
    return


async def full_userbase():
    user_docs = user_data.find()
    user_ids = []
    for doc in user_docs:
        user_ids.append(doc['_id'])
    return user_ids


async def del_user(user_id: int):
    user_data.delete_one({'_id': user_id})
    return


# --- Token Verification Functions ---

async def is_user_verified(user_id: int) -> bool:
    user = user_data.find_one({'_id': user_id})
    if not user:
        return False
    verify_status = user.get("verify_status", {})
    is_verified = verify_status.get("is_verified", False)
    verified_time = verify_status.get("verified_time", 0)
    
    # Check korbe time expire hoyeche kina (default 24 ghanta)
    if is_verified and (time.time() - verified_time) < VERIFY_EXPIRE:
        return True
    return False


async def update_verify_status(user_id: int, verify_token: str):
    user_data.update_one(
        {'_id': user_id},
        {
            '$set': {
                'verify_status.verify_token': verify_token,
                'verify_status.is_verified': False
            }
        },
        upsert=True
    )


async def get_verify_token(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if user:
        return user.get("verify_status", {}).get("verify_token")
    return None


async def set_verified(user_id: int):
    user_data.update_one(
        {'_id': user_id},
        {
            '$set': {
                'verify_status.is_verified': True,
                'verify_status.verified_time': time.time(),
                'verify_status.verify_token': ""
            }
        },
        upsert=True
    )


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
