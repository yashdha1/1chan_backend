from uuid import UUID

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger as log
from ..repo.post import PostRepository


class PostService:
    def __init__(self, db: AsyncSession, response: Response, r=None) -> None:
        self.db = db
        self.cache = r
        self.post_repo = PostRepository(self.db, self.cache)

    async def create_post(self, post_data: dict):
        try:
            res = await self.post_repo.create_post(post_data)
            log.info(f"Post created with ID: {res.id}")
            return res
        except Exception as e:
            log.error(f"Error creating post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_post_by_id(self, post_id: str):
        try:
            res = await self.post_repo.get_post_by_id(post_id)
            if not res:
                raise HTTPException(status_code=404, detail="Post not found")
            log.info(f"Post retrieved with ID: {res.id}")
            return res
        except HTTPException as he:
            log.error(f"Error fetching post: {he.detail}")
            raise he

    async def delete_post(self, uid: UUID, post_id: UUID):
        try:
            res = await self.post_repo.delete_post(post_id, uid)
            if not res:
                raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
            log.info(f"Post deleted with ID: {post_id}")
        except HTTPException as he:
            log.error(f"Error deleting post: {he.detail}")
            raise he
        except Exception as e:
            log.error(f"Error deleting post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def patch_post(
        self,
        post_id: UUID,
        uid: UUID,
        title: str | None = None,
        body: str | None = None,
        image_link: str | None = None,
        edited_by: str = "",
    ):
        try:
            res = await self.post_repo.patch_post(
                post_id, uid, title, body, image_link, edited_by
            )
            log.info(f"Post patched with ID: {post_id}")
            return res
        except HTTPException as he:
            log.error(f"Error patching post: {he.detail}")
            raise he
        except Exception as e:
            log.error(f"Error patching post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def like_post(self, post_id: UUID, user_id: UUID):
        try:
            res = await self.post_repo.like_post(post_id, user_id)
            log.info(f"Post liked: {post_id} by {user_id}")
            return res
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error liking post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def unlike_post(self, post_id: UUID, user_id: UUID):
        try:
            res = await self.post_repo.unlike_post(post_id, user_id)
            log.info(f"Post unliked: {post_id} by {user_id}")
            return res
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error unliking post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def search_posts(self, query: str):
        try:
            res = await self.post_repo.search_posts(query)
            log.info(f"Search completed for query: {query} with {len(res)} results")
            return res
        except Exception :
            log.exception(f"Error searching posts for query: {query}")
            raise HTTPException(status_code=500, detail="Internal Server Error")