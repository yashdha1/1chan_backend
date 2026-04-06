from urllib.parse import quote
import httpx
from ..core.config import settings
 
 
class AsyncClient:
    @staticmethod
    async def map_post_to_feed(new_post) -> dict | None:
        try:
            tags = [t for t in (new_post.tags or "").split(",") if t]
            print(f"Mapping post ID {new_post.id} to feed with tags: {tags}")
            payload = {
                "post_id": str(new_post.id),
                "tags": tags,
            }
            async with httpx.AsyncClient() as client:
                url = f"{settings.FEED_SERVICE_URL}/operation/post_add_tags"
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                print(f"Successfully mapped post ID {new_post.id} to feed with tags: {tags}")
                return result
        except httpx.HTTPError as e:
            print(f"HTTP error while mapping post to feed tags: {e}")
            return None

    @staticmethod
    async def get_feed_for_user(user_id: str, feed_type: str) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.FEED_SERVICE_URL}/generate_feed/{str(feed_type)}"
                response = await client.get(url, params={"user_id": user_id})
                response.raise_for_status()
                result = response.json()
                print(f"Successfully retrieved feed for user ID {user_id} with type {feed_type}")
                return result
        except httpx.HTTPError as e:
            print(f"HTTP error while retrieving feed for user ID {user_id}: {e}")
            return None
    
    @staticmethod
    async def send_notification(data) : 
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.NOTIFICATION_SERVICE_URL}/send"
                response = await client.post(url, json=data)
                response.raise_for_status()
                print(f"Successfully sent notification with data: {data}")
        except httpx.HTTPError as e:
            print(f"HTTP error while sending notification: {e}")

    @staticmethod
    async def get_user_by_username(username: str) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.AUTH_SERVICE_URL}/profile/{username}"
                response = await client.get(url)
                response.raise_for_status()
                return response.json().get("user")
        except httpx.HTTPError:
            return None