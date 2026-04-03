import random

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.logger import logger as log
from ..repo.feed import FeedRepository
from ..schema.feed import FeedResponse
from ..core.time import timer

class FeedService:
    def __init__(self, db: AsyncSession):
        self.repo = FeedRepository(db)

    async def generate_feed(self, user_id, feed_type: str) -> FeedResponse:
        try:
            if feed_type == "suggested":
                return await self._suggested(user_id)
            if feed_type == "latest":
                return await self._latest(user_id)
            if feed_type == "community":
                return await self._community(user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"generate_feed error error: {e}")
            raise HTTPException(status_code=500, detail="Feed generation failed")

    @timer
    async def _suggested(self, user_id) -> FeedResponse:
        # 1. get user tag weights 
        weights = await self.repo.get_user_weights(user_id)

        if not weights: # user has no history: 
            pool = await self.repo.get_cold_start_pool(
                user_id, settings.COLD_START_SIZE
            )
            return FeedResponse(post_ids=pool, has_more=len(pool) == settings.COLD_START_SIZE)

        # sort by weightt
        sorted_tags = sorted(weights.items(), key=lambda kv: kv[1], reverse=True) 

        # 2. get top k tags
        top_k_user_tags = []
        for tag, weight in sorted_tags : 
            top_k_user_tags.append(tag)
            if len(top_k_user_tags) == settings.TOP_K_USER_TAGS:
                break
        
        # 3. get preference pool
        pref_limit = settings.FEED_TOTAL_PAGE_SIZE - settings.EXPLORE_FEED_SIZE
        n_tags = len(top_k_user_tags)
        per_tag = max(1, (pref_limit + n_tags - 1) // n_tags) if n_tags else pref_limit
        pref_pool: list[int] = []
        for tid in top_k_user_tags:
            if len(pref_pool) >= pref_limit:
                break
            cap = min(per_tag, pref_limit - len(pref_pool))
            bucket = await self.repo.get_preference_pool_for_tag(
                tid, user_id, cap, exclude_post_ids=pref_pool or None
            )
            pref_pool.extend(bucket)

        # 4. get random pool
        rand_pool = await self.repo.get_random_pool(
            user_id, pref_pool, settings.EXPLORE_FEED_SIZE
        )

        # 5. combined 
        combined = pref_pool + rand_pool
        random.shuffle(combined)
        return FeedResponse(
            post_ids=combined,
            has_more=len(combined) == settings.FEED_TOTAL_PAGE_SIZE,
        )

    @timer
    async def _latest(self, user_id) -> FeedResponse:
        pool = await self.repo.get_latest_pool(user_id, settings.FEED_TOTAL_PAGE_SIZE)
        return FeedResponse(post_ids=pool, has_more=len(pool) == settings.FEED_TOTAL_PAGE_SIZE)
    
    @timer
    async def _community(self, user_id) -> FeedResponse:
        pool = await self.repo.get_community_pool(user_id, settings.FEED_TOTAL_PAGE_SIZE)
        return FeedResponse(post_ids=pool, has_more=len(pool) == settings.FEED_TOTAL_PAGE_SIZE)

    # Operations CRUD
    async def mark_viewed(self, user_id, post_ids: list[int]):
        try:
            await self.repo.mark_viewed(user_id, post_ids)
        except Exception as e:
            log.error(f"mark_viewed error: {e}")
            raise HTTPException(status_code=500, detail="Failed to mark posts viewed")

    async def update_weights(self, user_id, tags: list[str], operation: str):
        weight_map = {"like": 1, "dislike": -1, "comment": 4}
        delta_val = weight_map.get(operation, 1)
        delta = {t: delta_val for t in tags}
        try:
            await self.repo.upsert_weights(user_id, delta)
        except Exception as e:
            log.error(f"update_weights error: {e}")
            raise HTTPException(status_code=500, detail="Failed to update weights")

    async def add_tag(self, name: str):
        try:
            await self.repo.add_tag(name)
        except Exception as e:
            log.error(f"add_tag error: {e}")
            raise HTTPException(status_code=500, detail="Failed to add tag")

    async def add_post_tags(self, post_id: int, tag_names: list[str]):
        try:
            await self.repo.add_post_tags(post_id, tag_names)
        except Exception as e:
            log.error(f"add_post_tags error: {e}")
            raise HTTPException(status_code=500, detail="Failed to add post tags")

    async def get_tags(self):
        try:
            rows = await self.repo.get_all_tags()
            return [{"id": r.id, "name": r.name, "post_count": r.post_count} for r in rows]
        except Exception as e:
            log.error(f"get_tags error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tags")
