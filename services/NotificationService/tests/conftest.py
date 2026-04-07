"""Shared fixtures for NotificationService tests."""

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

# ── Env vars ─────────────────────────────────────────────────────────
os.environ.update({
    "POSTGRES_NOTIFICATION_USERNAME": "test",
    "POSTGRES_NOTIFICATION_PASSWORD": "test",
    "POSTGRES_NOTIFICATION_HOST": "localhost",
    "POSTGRES_NOTIFICATION_PORT": "5434",
    "POSTGRES_NOTIFICATION_DATABASE": "TestNotifDB",
    "JWT_PUBLIC_KEY": PUBLIC_PEM,
    "REDIS_STREAM_HOST": "localhost",
    "REDIS_STREAM_PORT": "6381",
})

# Patch consume before app import
import src.lib.consume as _consume_mod  # noqa: E402
_consume_mod.redis_client = AsyncMock()
_consume_mod.consume = AsyncMock()

from src.lib.db import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402

# ── SQLite in-memory ─────────────────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///file:notiftest?mode=memory&cache=shared&uri=true"
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


@pytest_asyncio.fixture()
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def make_token(user_id: str | None = None, username: str = "tester", role: str = "user"):
    now = datetime.now(timezone.utc)
    payload = {
        "id": user_id or str(uuid.uuid4()),
        "username": username,
        "role": role,
        "avatar": "",
        "iss": "1chan-server",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, PRIVATE_PEM, algorithm="RS256")


USER_ID = str(uuid.uuid4())


def auth_cookies(user_id: str = USER_ID):
    return {"access_token": make_token(user_id=user_id)}
