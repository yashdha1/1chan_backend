"""cache puroposes"""

from redis.asyncio import Redis

r = Redis(host="localhost", port=6380, db=0)

def get_redis() -> Redis:
    return r