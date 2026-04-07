# CONSUMER : 

import asyncio
import os
from redis.asyncio import Redis 
import json
from uuid import UUID
from .db import AsyncSessionLocal
from ..core.logger import logger as log
from ..schema.notification import SendNotificationRequest
from ..service.notification import NotificationService

STREAM = "group:notification:send"
GROUP = "notification-service-group"
CONSUMER = "notification-service-1"   


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
    try:
        request = SendNotificationRequest(
            user_id=UUID(str(event_data["user_id"])),
            publisher_id=UUID(str(event_data["publisher_id"])),
            publisher_name=event_data["publisher_name"],
            user_name=event_data["user_name"],
            type=event_data["type"],
            post_id=UUID(str(event_data["post_id"])),
            post_title=event_data["post_title"],
            body=event_data.get("body"),
        )

        async with AsyncSessionLocal() as db:
            await NotificationService.send_notification(db, request)

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