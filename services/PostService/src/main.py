import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .lib.consume import consume

from .api.router import router
from .api.v1.post_manager import ws_router
from .core.config import settings
from .core.logger import logger as log
from .lib.db import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    task = asyncio.create_task(consume())
    task.add_done_callback(
        lambda t: log.error(f"Profile consumer task stopped: {t.exception()}")
        if t.exception() else None
    )

    yield

    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# Middleware for CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/posts")
app.include_router(ws_router) # socket routes :