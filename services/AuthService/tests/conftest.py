"""Shared fixtures for AuthService tests."""

import os, uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# ── Generate RSA key pair for tests ──────────────────────────────────
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

# ── Patch env BEFORE any service module is imported ──────────────────
os.environ.update({
    "POSTGRES_AUTH_USERNAME": "test",
    "POSTGRES_AUTH_PASSWORD": "test",
    "POSTGRES_AUTH_HOST": "localhost",
    "POSTGRES_AUTH_PORT": "5432",
    "POSTGRES_AUTH_DATABASE": "TestAuthDB",
    "JWT_PUBLIC_KEY": PUBLIC_PEM,
    "JWT_PRIVATE_KEY": PRIVATE_PEM,
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7",
    "REDIS_AUTH_HOST": "localhost",
    "REDIS_AUTH_PORT": "6379",
    "REDIS_STREAM_HOST": "localhost",
    "REDIS_STREAM_PORT": "6381",
})

from src.lib.db import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.lib.redis import get_redis  # noqa: E402
from src.core.config import settings  # noqa: E402

# ── In-memory SQLite engine ──────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///file:authtest?mode=memory&cache=shared&uri=true"
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


def make_access_token(user_id: str | None = None, username: str = "tester", role: str = "user", avatar: str = ""):
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


def make_refresh_token(user_id: str, username: str = "tester", role: str = "user"):
    now = datetime.now(timezone.utc)
    payload = {
        "id": user_id,
        "username": username,
        "role": role,
        "iss": "1chan-server",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=7)).timestamp()),
    }
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256")
