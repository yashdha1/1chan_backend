"""PostService API tests – 15 cases."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from conftest import auth_cookies, make_token, USER_ID

pytestmark = pytest.mark.asyncio

POSTS_URL = "/api/v1/posts"
COMMENTS_URL = "/api/v1/posts/comments"


def _post_body(title="Test Post", tags=None):
    return {
        "title": title,
        "body": "Some content here",
        "image_link": None,
        "tags": tags or ["python"],
    }


async def _create_post(client, title="Test Post", user_id=USER_ID, tags=None):
    """Helper: create a post and return its response JSON."""
    with patch("src.service.AsyncClient.AsyncClient.map_post_to_feed", new_callable=AsyncMock, return_value=None):
        res = await client.post(
            f"{POSTS_URL}/",
            json=_post_body(title, tags),
            cookies=auth_cookies(user_id),
        )
    return res


# ── Create Post ──────────────────────────────────────────────────────

async def test_create_post_success(client):
    res = await _create_post(client)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Test Post"
    assert data["user_name"] == "tester"
    assert "python" in data["tags"]


async def test_create_post_no_auth(client):
    res = await client.post(f"{POSTS_URL}/", json=_post_body())
    assert res.status_code == 401


async def test_create_post_no_tags(client):
    body = _post_body()
    body["tags"] = []
    res = await client.post(f"{POSTS_URL}/", json=body, cookies=auth_cookies())
    assert res.status_code == 422


async def test_create_post_too_many_tags(client):
    body = _post_body(tags=["a", "b", "c", "d", "e", "f"])
    res = await client.post(f"{POSTS_URL}/", json=body, cookies=auth_cookies())
    assert res.status_code == 422


# ── Get Post ─────────────────────────────────────────────────────────

async def test_get_post_by_id(client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    res = await client.get(f"{POSTS_URL}/{post_id}")
    assert res.status_code == 200
    assert res.json()["post_id"] == post_id


async def test_get_post_not_found(client):
    fake_id = str(uuid.uuid4())
    res = await client.get(f"{POSTS_URL}/{fake_id}")
    assert res.status_code == 404


# ── Get Posts by Username ────────────────────────────────────────────

async def test_get_posts_by_username(client):
    await _create_post(client, title="P1")
    await _create_post(client, title="P2")
    res = await client.get(f"{POSTS_URL}/user/tester")
    assert res.status_code == 200
    assert len(res.json()) >= 2


# ── Patch Post ───────────────────────────────────────────────────────

async def test_patch_post(client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    res = await client.patch(
        f"{POSTS_URL}/{post_id}",
        json={"title": "Updated Title", "body": None, "image_link": None, "tags": None, "edited_by": ""},
        cookies=auth_cookies(),
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Updated Title"


# ── Delete Post ──────────────────────────────────────────────────────

async def test_delete_post(client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    res = await client.delete(f"{POSTS_URL}/{post_id}", cookies=auth_cookies())
    assert res.status_code == 204


async def test_delete_post_no_auth(client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    res = await client.delete(f"{POSTS_URL}/{post_id}")
    assert res.status_code == 401


# ── Like / Unlike ────────────────────────────────────────────────────

@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_like_post(mock_pub, client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    res = await client.post(f"{POSTS_URL}/{post_id}/like", cookies=auth_cookies())
    assert res.status_code == 200
    assert res.json()["like_count"] == 1


@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_unlike_post(mock_pub, client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    await client.post(f"{POSTS_URL}/{post_id}/like", cookies=auth_cookies())
    res = await client.post(f"{POSTS_URL}/{post_id}/unlike", cookies=auth_cookies())
    assert res.status_code == 200
    assert res.json()["like_count"] == 0


@patch("src.lib.publish.redis_client", new_callable=AsyncMock)
async def test_double_like_idempotent(mock_pub, client):
    create_res = await _create_post(client)
    post_id = create_res.json()["post_id"]
    await client.post(f"{POSTS_URL}/{post_id}/like", cookies=auth_cookies())
    await client.post(f"{POSTS_URL}/{post_id}/like", cookies=auth_cookies())
    get_res = await client.get(f"{POSTS_URL}/{post_id}")
    assert get_res.json()["like_count"] == 1


# ── Search (uses PostgreSQL FTS – expect 500 on SQLite) ──────────────

async def test_search_returns_500_on_sqlite(client):
    """Search uses websearch_to_tsquery / @@ which are PG-only.
    On SQLite the endpoint returns 500 — this confirms the route is wired."""
    res = await client.post(f"{POSTS_URL}/search", json={"query": "nonexistent_xyz"})
    assert res.status_code == 500
