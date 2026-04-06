"""redis pub sub model ke liye"""

from redis.asyncio import Redis

r = Redis(host="localhost", port=6381, db=0)

def get_redis() -> Redis:
    return r