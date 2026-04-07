# user_service/events/publisher.py

import os
from redis.asyncio import Redis 
import json
 

redis_client = Redis(
    host=os.getenv("REDIS_STREAM_HOST", "localhost"),
    port=int(os.getenv("REDIS_STREAM_PORT", "6381")),
    db=0,
)


async def publish_notification(user_id: str, post_id: str, publisher_id: str, publisher_name: str, user_name: str, type: str, post_title: str, body: str | None = None):
    payload = {
        "user_id": user_id,
        "post_id": post_id,
        "publisher_id": publisher_id,
        "publisher_name": publisher_name,
        "user_name": user_name,
        "type": type,
        "post_title": post_title,
        "body": body,
    }
    await redis_client.xadd(
        "group:notification:send",        # notification group
        {"data": json.dumps(payload)}
    )