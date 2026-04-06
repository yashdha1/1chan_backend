"""redis pub sub model ke liye"""

from redis.asyncio import Redis
from ..core.config import settings

r = Redis(
    host=settings.REDIS_PS_HOST,
    port=settings.REDIS_PS_PORT,
    db=settings.REDIS_PS_DB,
    health_check_interval=30,
)

def get_redis() -> Redis:
    return r