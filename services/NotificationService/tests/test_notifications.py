"""NotificationService API tests – 12 cases."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from conftest import auth_cookies, make_token, USER_ID, TestSession
from src.models.notifcation import Notification

pytestmark = pytest.mark.asyncio

BASE = "/api/v1/notifications"


async def _seed_notification(user_id: str, notif_type: str = "like") -> str:
    """Insert a notification row via ORM and return its id."""
    nid = uuid.uuid4()
    pub_id = uuid.uuid4()
    post_id = uuid.uuid4()
    async with TestSession() as s:
        n = Notification(
            id=nid,
            user_id=uuid.UUID(user_id),
            publisher_id=pub_id,
            publisher_name="publisher1",
            user_name="user1",
            type=notif_type,
            post_id=post_id,
            post_title="Test Post",
            is_read="false",
        )
        s.add(n)
        await s.commit()
    return str(nid)


# ── Get Notifications ────────────────────────────────────────────────

async def test_get_notifications_empty(client):
    res = await client.post(f"{BASE}/activity/0", cookies=auth_cookies())
    assert res.status_code == 200
    assert res.json() == []


async def test_get_notifications_with_data(client):
    await _seed_notification(USER_ID, "like")
    await _seed_notification(USER_ID, "comment")
    res = await client.post(f"{BASE}/activity/0", cookies=auth_cookies())
    assert res.status_code == 200
    assert len(res.json()) == 2


async def test_get_notifications_pagination(client):
    for _ in range(3):
        await _seed_notification(USER_ID)
    res = await client.post(f"{BASE}/activity/2", cookies=auth_cookies())
    assert res.status_code == 200
    assert len(res.json()) <= 15


async def test_get_notifications_no_auth(client):
    res = await client.post(f"{BASE}/activity/0")
    assert res.status_code == 401


# ── Notifications belong to user only ────────────────────────────────

async def test_notifications_isolated_per_user(client):
    other_user = str(uuid.uuid4())
    await _seed_notification(other_user, "like")
    res = await client.post(f"{BASE}/activity/0", cookies=auth_cookies())
    assert res.status_code == 200
    assert len(res.json()) == 0


# ── Mark as Read ─────────────────────────────────────────────────────

async def test_mark_as_read(client):
    nid = await _seed_notification(USER_ID)
    res = await client.post(
        f"{BASE}/mark",
        json={"notification_id": nid},
        cookies=auth_cookies(),
    )
    assert res.status_code == 200


async def test_mark_as_read_not_found(client):
    fake_id = str(uuid.uuid4())
    res = await client.post(
        f"{BASE}/mark",
        json={"notification_id": fake_id},
        cookies=auth_cookies(),
    )
    assert res.status_code == 404


async def test_mark_as_read_no_auth(client):
    nid = await _seed_notification(USER_ID)
    res = await client.post(f"{BASE}/mark", json={"notification_id": nid})
    assert res.status_code == 401


async def test_mark_as_read_wrong_user(client):
    other_user = str(uuid.uuid4())
    nid = await _seed_notification(other_user)
    res = await client.post(
        f"{BASE}/mark",
        json={"notification_id": nid},
        cookies=auth_cookies(),
    )
    assert res.status_code == 404


# ── Notification types ───────────────────────────────────────────────

async def test_notification_types_returned(client):
    await _seed_notification(USER_ID, "like")
    await _seed_notification(USER_ID, "comment")
    await _seed_notification(USER_ID, "mention")
    res = await client.post(f"{BASE}/activity/0", cookies=auth_cookies())
    types = {n["type"] for n in res.json()}
    assert types == {"like", "comment", "mention"}


# ── Validation ───────────────────────────────────────────────────────

async def test_mark_invalid_uuid(client):
    res = await client.post(
        f"{BASE}/mark",
        json={"notification_id": "not-a-uuid"},
        cookies=auth_cookies(),
    )
    assert res.status_code == 422


async def test_activity_invalid_offset(client):
    res = await client.post(f"{BASE}/activity/abc", cookies=auth_cookies())
    assert res.status_code == 422
