import re
from uuid import UUID

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger as log
from ..models.comment import Comment
from ..repo.comment import CommentRepository
from ..repo.post import PostRepository
from .AsyncClient import AsyncClient
from ..lib.publish import publish_notification

INTERNAL_SERVER_ERROR = "Internal Server Error"


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
            res = await self.comment_repo.create_comment(
                post_id, parent_id, user_id, user_name, user_avatar, body
            )
            log.info(f"Comment created with ID: {res.id}")

            post = await PostRepository(self.db).get_post_by_id(post_id)
            notified: set[str] = {str(user_id)}  # never notify the actor

            base = {
                "publisher_id": str(user_id),
                "publisher_name": user_name,
                "user_name": user_name,
                "post_id": str(post_id),
                "post_title": post.title if post else "",
            }

            # 1. notify post owner
            if post and str(post.user_id) not in notified:
                await publish_notification(**base, user_id=str(post.user_id), type="comment")
                notified.add(str(post.user_id))
                log.info(f"Notification sent to post owner with ID: {post.user_id} for comment ID: {res.id}")

            # 2. notify parent comment author (reply)
            if parent_id:
                parent = await self.comment_repo.get_comment_by_id(parent_id)
                if parent and str(parent.user_id) not in notified:
                    await publish_notification(**base, user_id=str(parent.user_id), type="reply")
                    notified.add(str(parent.user_id))
                    log.info(f"Notification sent to parent comment author with ID: {parent.user_id} for comment ID: {res.id}")

            # 3. notify @mentioned users
            for username in set(re.findall(r"@(\w+)", body)):
                mentioned = await AsyncClient.get_user_by_username(username)
                if mentioned and str(mentioned["id"]) not in notified:
                    await publish_notification(**base, user_id=str(mentioned["id"]), type="mention", body=body)
                    notified.add(str(mentioned["id"]))
                    log.info(f"Notification sent to mentioned user with ID: {mentioned['id']} for comment ID: {res.id}")

            return res
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error creating comment: {e}")
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

    async def list_for_post(self, post_id: UUID, offset: int, parent_id: UUID) -> list[Comment]:
        try:
            return await self.comment_repo.list_for_post(post_id, offset, parent_id)
        except Exception as e:
            log.error(f"Error listing comments: {e}")
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

    async def delete_comment(self, comment_id: UUID, user_id: UUID, role: str) -> None:
        try:
            can_delete_any = role in {"admin", "mod"}
            await self.comment_repo.delete_comment(comment_id, user_id, can_delete_any)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error deleting comment: {e}")
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

    async def like_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        try:
            return await self.comment_repo.like_comment(comment_id, user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error liking comment: {e}")
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)

    async def unlike_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        try:
            return await self.comment_repo.unlike_comment(comment_id, user_id)
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error unliking comment: {e}")
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR)
