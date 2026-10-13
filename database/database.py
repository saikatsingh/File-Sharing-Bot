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


# --- User Ban / Unban System ---

async def ban_user(user_id: int):
    user_data.update_one(
        {'_id': int(user_id)},
        {'$set': {'banned': True}},
        upsert=True
    )


async def unban_user(user_id: int):
    user_data.update_one(
        {'_id': int(user_id)},
        {'$set': {'banned': False}},
        upsert=True
    )


async def is_banned(user_id: int) -> bool:
    user = user_data.find_one({'_id': int(user_id)})
    return bool(user and user.get('banned', False))


# --- Database Stats & Storage Info ---

async def get_db_stats():
    """MongoDB cluster storage ebong user count calculate kore"""
    try:
        stats = database.command("dbStats")
        data_size = stats.get("dataSize", 0) / (1024 * 1024)       # MB
        storage_size = stats.get("storageSize", 0) / (1024 * 1024) # MB
    except Exception:
        data_size = 0.0
        storage_size = 0.0

    total_users = user_data.count_documents({})
    banned_users = user_data.count_documents({'banned': True})
    premium_users = user_data.count_documents({'is_premium': True})

    # MongoDB Atlas free cluster limit 512 MB
    free_limit = 512.0
    free_storage = max(0.0, free_limit - storage_size)

    return {
        "users": total_users,
        "banned": banned_users,
        "premium": premium_users,
        "data_size": round(data_size, 2),
        "storage_size": round(storage_size, 2),
        "free_storage": round(free_storage, 2)
    }


# --- Clear Database Cache / Temporary Data ---

async def clear_database_posts():
    """Purono temporary verification tokens ebong daily quota cache purge kore"""
    result = user_data.update_many(
        {},
        {
            '$unset': {
                'verify_status': "",
                'last_free_time': ""
            }
        }
    )
    return result.modified_count


# --- Token Verification Functions ---

async def is_user_verified(user_id: int) -> bool:
    user = user_data.find_one({'_id': user_id})
    if not user:
        return False
    verify_status = user.get("verify_status", {})
    is_verified = verify_status.get("is_verified", False)
    verified_time = verify_status.get("verified_time", 0)
    
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

    if time.time() < expire_time:
        return True
    else:
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


# --- 24 Hours Daily 1 Free File Usage Tracking ---

async def get_free_usage_status(user_id: int) -> int:
    """User-er 24 ghontay 1-ti free file quota baki ache kina check korbe (Return: 1 or 0)"""
    user = user_data.find_one({'_id': user_id})
    if not user:
        return 1
    last_free_time = user.get("last_free_time", 0)
    if (time.time() - last_free_time) >= 86400:
        return 1
    return 0


async def use_free_quota(user_id: int):
    """User free file claim korle timestamp update kore quota 0 kore debe"""
    user_data.update_one(
        {'_id': user_id},
        {'$set': {'last_free_time': time.time()}},
        upsert=True
    )
