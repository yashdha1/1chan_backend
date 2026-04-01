from uuid import UUID

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger as log
from ..models.comment import Comment
from ..repo.comment import CommentRepository


class CommentService:
    def __init__(self, db: AsyncSession, response: Response, r=None) -> None:
        self.db = db
        self.cache = r
        self.comment_repo = CommentRepository(self.db, self.cache)

    async def create_comment(
        self,
        post_id: UUID,
        parent_id: UUID | None,
        user_id: UUID,
        user_name: str,
        user_avatar: str | None,
        body: str,
    ) -> Comment:
        try:
            return await self.comment_repo.create_comment(
                post_id, parent_id, user_id, user_name, user_avatar, body
            )
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error creating comment: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def list_for_post(self, post_id: UUID, offset: int) -> list[Comment]:
        try:
            return await self.comment_repo.list_for_post(post_id, offset)
        except Exception as e:
            log.error(f"Error listing comments: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> None:
        try:
            await self.comment_repo.delete_comment(comment_id, user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error deleting comment: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def like_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        try:
            return await self.comment_repo.like_comment(comment_id, user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error liking comment: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def unlike_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        try:
            return await self.comment_repo.unlike_comment(comment_id, user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error unliking comment: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
