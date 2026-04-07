"""Shared fixtures for PostService tests."""

import os, uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# ── RSA key pair ─────────────────────────────────────────────────────
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_PEM = _private_key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
PUBLIC_PEM = (
    _private_key.public_key()
    .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    .decode()
)

# ── Env vars BEFORE imports ──────────────────────────────────────────
os.environ.update({
    "POSTGRES_POST_USERNAME": "test",
    "POSTGRES_POST_PASSWORD": "test",
    "POSTGRES_POST_HOST": "localhost",
    "POSTGRES_POST_PORT": "5433",
    "POSTGRES_POST_DATABASE": "TestPostDB",
    "JWT_PUBLIC_KEY": PUBLIC_PEM,
    "REDIS_POST_HOST": "localhost",
    "REDIS_POST_PORT": "6380",
    "REDIS_STREAM_HOST": "localhost",
    "REDIS_STREAM_PORT": "6381",
    "FEED_SERVICE_URL": "http://fake-feed:8004/api/v1/feed",
    "NOTIFICATION_SERVICE_URL": "http://fake-notif:8002/api/v1/notifications",
    "AUTH_SERVICE_URL": "http://fake-auth:8001/api/v1",
})

# Patch the redis stream client in publish before it connects
import src.lib.publish as _pub_mod  # noqa: E402
_pub_mod.redis_client = AsyncMock()

# Patch the redis stream in consume so lifespan doesn't explode
import src.lib.consume as _consume_mod  # noqa: E402
_consume_mod.redis_client = AsyncMock()
_consume_mod.consume = AsyncMock()  # prevent background task

from src.lib.db import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.lib.redis import get_redis  # noqa: E402

# ── Make PostgreSQL-only types work on SQLite ────────────────────────
from sqlalchemy.dialects.postgresql import TSVECTOR  # noqa: E402
from sqlalchemy import String, event  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402


@compiles(TSVECTOR, "sqlite")
def _compile_tsvector_sqlite(element, compiler, **kw):
    return "TEXT"


# Drop Computed columns from Post.search_vector for SQLite tests
# (SQLite can't handle PostgreSQL computed expressions)
from src.models.post import Post  # noqa: E402
_sv_col = Post.__table__.c.get("search_vector")
if _sv_col is not None:
    _sv_col.server_default = None
    _sv_col.computed = None  # type: ignore[assignment]

# ── SQLite in-memory ─────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///file:posttest?mode=memory&cache=shared&uri=true"
test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db():
    async with TestSession() as session:
        yield session


@pytest.fixture()
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    r.delete = AsyncMock()
    return r


@pytest_asyncio.fixture()
async def client(mock_redis):
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def make_token(user_id: str | None = None, username: str = "tester", role: str = "user", avatar: str = ""):
    now = datetime.now(timezone.utc)
    payload = {
        "id": user_id or str(uuid.uuid4()),
        "username": username,
        "role": role,
        "avatar": avatar,
        "iss": "1chan-server",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256")

USER_ID = str(uuid.uuid4())
TOKEN = None  # set per-test


def auth_cookies(user_id: str = USER_ID, username: str = "tester"):
    return {"access_token": make_token(user_id=user_id, username=username)}
