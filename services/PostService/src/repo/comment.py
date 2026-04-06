from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from ..models.comment import Comment, CommentLike
from ..models.post import Post
from ..core.logger import logger as log


class CommentRepository:
    def __init__(self, db: AsyncSession, cache=None):
        self.db = db
        self.cache = cache

    async def create_comment(
        self,
        post_id: UUID,
        parent_id: UUID | None,
        user_id: UUID,
        user_name: str,
        user_avatar: str | None,
        body: str,
    ) -> Comment:
        pq = select(Post).where(Post.id == post_id)
        pr = await self.db.execute(pq)
        post = pr.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if parent_id is not None:
            cq = select(Comment).where(
                Comment.id == parent_id, Comment.post_id == post_id
            )
            cr = await self.db.execute(cq)
            if not cr.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Parent comment not found")

        comment = Comment(
            post_id=post_id,
            parent_id=parent_id,
            user_id=user_id,
            user_name=user_name,
            user_avatar=user_avatar,
            body=body,
        )
        self.db.add(comment)
        post.comment_count = int(post.comment_count or 0) + 1
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(comment)
        log.info(f"Comment created id={comment.id} post_id={post_id}")
        return comment

    async def list_for_post(self, post_id: UUID, ofset: int, parent_id: UUID | None) -> list[Comment]:

        # TODO : cache the res for this query in the global cache : invalidate after like 2 hrs : # noqa E501
        q = (
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_id == parent_id)
            .order_by(Comment.like_count.desc())
            .offset(ofset)
            .limit(15)
        )
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> None:
        q = select(Comment).where(Comment.id == comment_id, Comment.user_id == user_id)
        res = await self.db.execute(q)
        comment = res.scalar_one_or_none()
        if not comment:
            raise HTTPException(
                status_code=404, detail="Comment not found or user unauthorized"
            )
        post_id = comment.post_id
        pq = select(Post).where(Post.id == post_id)
        pr = await self.db.execute(pq)
        post = pr.scalar_one_or_none()

        comment.body = "[deleted]" # update the status of the comment, instead of deleting to keep the comments history. 
        
        await self.db.commit()
        if post:
            post.comment_count = max(0, int(post.comment_count or 0) - 1)
            self.db.add(post)
        await self.db.commit()
        log.info(f"Comment deleted id={comment_id}")

    async def like_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        cq = select(Comment).where(Comment.id == comment_id)
        cr = await self.db.execute(cq)
        comment = cr.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        lq = select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
        )
        lr = await self.db.execute(lq)
        if lr.scalar_one_or_none():
            return comment

        self.db.add(CommentLike(comment_id=comment_id, user_id=user_id))
        comment.like_count = int(comment.like_count or 0) + 1
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def get_comment_by_id(self, comment_id: UUID) -> Comment | None:
        q = select(Comment).where(Comment.id == comment_id)
        res = await self.db.execute(q)
        return res.scalar_one_or_none()

    async def unlike_comment(self, comment_id: UUID, user_id: UUID) -> Comment:
        cq = select(Comment).where(Comment.id == comment_id)
        cr = await self.db.execute(cq)
        comment = cr.scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        lq = select(CommentLike).where(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
        )
        lr = await self.db.execute(lq)
        like_row = lr.scalar_one_or_none()
        if not like_row:
            return comment

        await self.db.delete(like_row)
        comment.like_count = max(0, int(comment.like_count or 0) - 1)
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        return comment
    