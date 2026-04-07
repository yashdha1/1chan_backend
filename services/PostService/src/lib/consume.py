# CONSUMER : 

import asyncio
import os
from redis.asyncio import Redis 
import json
from uuid import UUID
from .db import AsyncSessionLocal
from ..models.post import Post
from ..models.comment import Comment
from ..core.logger import logger as log
from sqlalchemy import update

STREAM = "user:profile:updated"
GROUP = "post-service-group"
CONSUMER = "post-service-1"   


redis_client = Redis(
    host=os.getenv("REDIS_STREAM_HOST", "localhost"),
    port=int(os.getenv("REDIS_STREAM_PORT", "6381")),
    db=0,
)


async def ensure_group():
    """Create consumer group if it doesn't exist."""
    try:
        await redis_client.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except Exception as e:
        if "BUSYGROUP" in str(e):
            ...  # Group already exists 
        else:
            raise


async def process_event(event_data: dict):
    try : 
        user_id = UUID(str(event_data["user_id"]))
        username = event_data["username"]
        profile_image = event_data.get("avatar")

        # Update denormalized user fields in posts table
        async with AsyncSessionLocal() as db:
            # update the posts
            stmt_1 = (
                update(Post)
                .where(Post.user_id == user_id)
                .values(user_name=username, user_avatar=profile_image)
            )

            # update the comments 
            stmt_2 = (
                update(Comment)
                .where(Comment.user_id == user_id)
                .values(user_name=username, user_avatar=profile_image)
            )
            await db.execute(stmt_1)
            log.info(f"Updated the username/avatar in POSTS for user_id={user_id}")
            await db.execute(stmt_2)
            log.info(f"Updated the username/avatar in COMMENTS for user_id={user_id}")
            await db.commit()
            
    except Exception as e: 
        log.error(f"Error processing event for user {event_data.get('user_id')}: {e}")

async def consume():
    group_ready = False

    # listen 
    while True:
        try:
            if not group_ready:
                await ensure_group()
                group_ready = True
                log.info(f"[{GROUP}] Listening on stream: {STREAM}")

            results = await redis_client.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={STREAM: ">"},  # ">" = only new/undelivered messages
                count=10,
                block=5000,
            )

            if not results:
                continue

            for stream_name, messages in results:
                for msg_id, fields in messages:
                    try:
                        payload = fields.get(b"data") or fields.get("data")
                        if payload is None:
                            raise ValueError("Missing 'data' field in stream message")
                        if isinstance(payload, bytes):
                            payload = payload.decode("utf-8")
                        data = json.loads(payload)
                        log.info(f"Processing profile update event message_id={msg_id}")
                        await process_event(data)
                        await redis_client.xack(STREAM, GROUP, msg_id)
                        log.info(f"Acknowledged profile update event message_id={msg_id}")

                    except Exception as e:
                        log.error(f"Failed to process {msg_id}: {e}") 

        except Exception as e:
            log.error(f"Consumer error: {e}")
            group_ready = False
            await asyncio.sleep(5)