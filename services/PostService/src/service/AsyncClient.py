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
