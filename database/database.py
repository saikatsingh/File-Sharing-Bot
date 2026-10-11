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
    
    # Check korbe time expire hoyeche kina
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


# --- Premium Subscription Functions (1D, 7D, 30D, 90D, 365D) ---

async def is_premium_user(user_id: int) -> bool:
    user = user_data.find_one({'_id': user_id})
    if not user:
        return False

    is_premium = user.get("is_premium", False)
    if not is_premium:
        return False

    expire_time = user.get("premium_expire", 0)

    # Current time-er sathe expiry check
    if time.time() < expire_time:
        return True
    else:
        # Time sesh hoye gele auto-remove premium
        user_data.update_one(
            {'_id': user_id},
            {
                '$set': {
                    'is_premium': False,
                    'premium_expire': 0
                }
            }
        )
        return False


async def add_premium(user_id: int, days: int = 30):
    # Jodi age thekei premium thake ebong validity thake, tobe tar sathe notun din jog hobe
    user = user_data.find_one({'_id': user_id})
    current_time = time.time()
    
    if user and user.get("is_premium", False) and user.get("premium_expire", 0) > current_time:
        new_expire = user["premium_expire"] + (days * 86400)
    else:
        new_expire = current_time + (days * 86400)

    user_data.update_one(
        {'_id': user_id},
        {
            '$set': {
                'is_premium': True,
                'premium_expire': new_expire
            }
        },
        upsert=True
    )


async def remove_premium(user_id: int):
    user_data.update_one(
        {'_id': user_id},
        {
            '$set': {
                'is_premium': False,
                'premium_expire': 0
            }
        }
    )


async def get_premium_status(user_id: int):
    user = user_data.find_one({'_id': user_id})
    if not user or not user.get("is_premium", False):
        return None
    expire_time = user.get("premium_expire", 0)
    remaining_seconds = expire_time - time.time()
    
    if remaining_seconds > 0:
        remaining_days = round(remaining_seconds / 86400, 1)
        if remaining_days >= 365:
            return "1 Year"
        return f"{remaining_days} Days"
    return "Expired"
