"""cache puroposes"""

import os
from redis.asyncio import Redis

r = Redis(
    host=os.getenv("REDIS_POST_HOST", "localhost"),
    port=int(os.getenv("REDIS_POST_PORT", "6380")),
    db=0,
)

def get_redis() -> Redis:
    return r