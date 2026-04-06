import asyncio
from contextlib import asynccontextmanager


from fastapi import FastAPI
from .core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from .lib.db import engine, Base
from .api.router import router
from .lib.message_queue import get_redis
from .core.logger import logger as log

async def notification_subscriber():
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("notifications")
    log.info("Subscribed to Redis notifications channel")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                log.info(f"Notification dispatched: {message['data']}")
    except asyncio.CancelledError:
        await pubsub.unsubscribe("notifications")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task = asyncio.create_task(notification_subscriber())

    yield

    task.cancel()

app = FastAPI(
    title = settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/notifications")