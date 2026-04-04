import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

_SRC_DIR = Path(__file__).resolve().parent.parent
_SERVICE_ROOT = _SRC_DIR.parent

for _env in (_SERVICE_ROOT / ".env", _SRC_DIR / ".env", Path(".env")):
    load_dotenv(_env)

_pg_user = os.environ["POSTGRES_FEED_USERNAME"]
_pg_pass = os.environ["POSTGRES_FEED_PASSWORD"]
_pg_host = os.getenv("POSTGRES_FEED_HOST", "localhost")
_pg_port = os.getenv("POSTGRES_FEED_PORT", "5435")
_pg_db = os.getenv("POSTGRES_FEED_DATABASE", "FeedDB")

DATABASE_URL = (
    f"postgresql+asyncpg://{_pg_user}:{_pg_pass}@{_pg_host}:{_pg_port}/{_pg_db}"
)

Base = declarative_base() 
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        try: 
            yield session 
        finally: 
            await session.close()