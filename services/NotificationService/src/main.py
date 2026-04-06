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
    while True:
        redis = get_redis()
        pubsub = redis.pubsub()
        try:
            await pubsub.subscribe("notifications")
            log.info("Subscribed to Redis notifications channel")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    log.info(f"Notification dispatched: {message['data']}")
        except asyncio.CancelledError:
            try:
                await pubsub.unsubscribe("notifications")
            finally:
                await pubsub.close()
            raise
        except Exception as e:
            log.warning(f"Redis subscriber unavailable: {e}. Retrying in 5s")
            await pubsub.close()
            await asyncio.sleep(5)

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/notifications")