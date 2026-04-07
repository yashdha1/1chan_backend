# user_service/events/publisher.py

import os
from redis.asyncio import Redis 
import json
 

redis_client = Redis(
    host=os.getenv("REDIS_STREAM_HOST", "localhost"),
    port=int(os.getenv("REDIS_STREAM_PORT", "6381")),
    db=0,
)

async def publish_user_updated(user_id: str, username: str, avatar: str):
    payload = {
        "user_id": user_id,
        "username": username,
        "avatar": avatar,
        "avatar_url": avatar,
    }
    await redis_client.xadd(
        "user:profile:updated",
        {"data": json.dumps(payload)}
    )