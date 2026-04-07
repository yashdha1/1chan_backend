"""AuthService API tests – 15 cases."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from conftest import make_access_token, make_refresh_token, PRIVATE_PEM

pytestmark = pytest.mark.asyncio

REG_URL = "/api/v1/free_auth/register"
LOGIN_URL = "/api/v1/free_auth/login"
REFRESH_URL = "/api/v1/free_auth/refresh"
PROFILE_URL = "/api/v1/auth/profile"
LOGOUT_URL = "/api/v1/auth/logout"
ADMIN_USERS_URL = "/api/v1/auth/admin/users"


def _reg_body(username: str = "alice", password: str = "securepass1"):
    return {
        "id": str(uuid.uuid4()),
        "username": username,
        "password": password,
        "bio": "hi",
        "avatar": "https://img.test/a.png",
        "role": "user",
    }


# ── Registration ─────────────────────────────────────────────────────

@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_register_success(mock_pub, client):
    res = await client.post(REG_URL, json=_reg_body())
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_register_duplicate_username(mock_pub, client):
    body = _reg_body("bob")
    await client.post(REG_URL, json=body)
    res = await client.post(REG_URL, json=_reg_body("bob"))
    assert res.status_code == 409


async def test_register_short_password(client):
    body = _reg_body(password="short")
    res = await client.post(REG_URL, json=body)
    assert res.status_code == 422


# ── Login ────────────────────────────────────────────────────────────

@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_login_success(mock_pub, client):
    await client.post(REG_URL, json=_reg_body("carol"))
    res = await client.post(LOGIN_URL, json={"username": "carol", "password": "securepass1"})
    assert res.status_code == 200
    assert "access_token" in res.json()


@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_login_wrong_password(mock_pub, client):
    await client.post(REG_URL, json=_reg_body("dave"))
    res = await client.post(LOGIN_URL, json={"username": "dave", "password": "wrongwrong"})
    assert res.status_code == 401


async def test_login_nonexistent_user(client):
    res = await client.post(LOGIN_URL, json={"username": "ghost", "password": "whatever1"})
    assert res.status_code == 401


# ── Profile ──────────────────────────────────────────────────────────

@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_get_profile(mock_pub, client):
    body = _reg_body("eve")
    await client.post(REG_URL, json=body)
    res = await client.get(f"{PROFILE_URL}/eve")
    assert res.status_code == 200
    assert res.json()["user"]["username"] == "eve"


async def test_get_profile_not_found(client):
    res = await client.get(f"{PROFILE_URL}/nobody")
    assert res.status_code == 404


@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_update_profile(mock_pub, client):
    body = _reg_body("frank")
    uid = body["id"]
    await client.post(REG_URL, json=body)
    token = make_access_token(user_id=uid, username="frank")
    res = await client.patch(
        PROFILE_URL,
        json={"username": "frank_updated", "bio": "new bio", "avatar": "https://img.test/b.png"},
        cookies={"access_token": token},
    )
    assert res.status_code == 200
    assert res.json()["user"]["username"] == "frank_updated"


# ── Auth required endpoints without token ────────────────────────────

async def test_update_profile_no_token(client):
    res = await client.patch(PROFILE_URL, json={"username": "x", "bio": "y", "avatar": "z"})
    assert res.status_code == 401


async def test_logout_no_token(client):
    res = await client.post(LOGOUT_URL)
    assert res.status_code == 401


async def test_delete_profile_no_token(client):
    res = await client.delete(PROFILE_URL)
    assert res.status_code == 401


# ── Admin ────────────────────────────────────────────────────────────

@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_admin_list_users(mock_pub, client):
    body = _reg_body("grace")
    await client.post(REG_URL, json=body)
    admin_token = make_access_token(role="admin", username="admin1")
    res = await client.get(f"{ADMIN_USERS_URL}/all", cookies={"access_token": admin_token})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_admin_forbidden_for_normal_user(client):
    token = make_access_token(role="user")
    res = await client.get(f"{ADMIN_USERS_URL}/all", cookies={"access_token": token})
    assert res.status_code == 403
