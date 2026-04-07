"""primarily for the tokens."""

import os
from redis.asyncio import Redis

r = Redis(
    host=os.getenv("REDIS_AUTH_HOST", "localhost"),
    port=int(os.getenv("REDIS_AUTH_PORT", "6379")),
    db=0,
)


def get_redis() -> Redis:
    return r
