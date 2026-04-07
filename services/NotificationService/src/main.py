from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from .core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from .lib.db import engine, Base
from .api.router import router
from .lib.consume import consume
from .core.logger import logger as log

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start the Redis consumer as a background task
    consumer_task = asyncio.create_task(consume())
    log.info("Redis notification consumer started")
    
    yield
    
    # Cleanup: cancel the consumer task on shutdown
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        log.info("Redis notification consumer stopped")

app = FastAPI(
    title = settings.PROJECT_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/notifications")