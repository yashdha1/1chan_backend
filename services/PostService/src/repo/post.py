import json
from uuid import UUID

from sqlalchemy import select, func
# from sqlalchemy.ext.asyncio import AsyncSession # noqa F401

from ..models.post import Post, PostLike
from fastapi import HTTPException
from ..core.logger import logger as log


class PostRepository:
    def __init__(self, db, cache=None):
        self.db = db
        self.cache = cache

    async def create_post(self, post_data):
        print(post_data)
        new_post = Post(**post_data)
        self.db.add(new_post)
        await self.db.commit()
        await self.db.refresh(new_post)
        return new_post

    async def get_post_by_id(self, post_id):
        q = select(Post).where(Post.id == UUID(str(post_id)))
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        return post

    async def get_posts_by_ids_ordered(self, ids: list[UUID]) -> list[Post]:
        if not ids:
            return []
        q = select(Post).where(Post.id.in_(ids))
        res = await self.db.execute(q)
        by_id = {p.id: p for p in res.scalars().all()}
        return [by_id[i] for i in ids if i in by_id]

    async def delete_post(self, post_id, user_id):
        q = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
        await self.db.delete(post)
        await self.db.commit()
        return True

    async def patch_post(
        self,
        post_id,
        user_id,
        title: str | None = None,
        body: str | None = None,
        image_link: str | None = None,
        edited_by: str = "",
        tags: str | None = None,
    ):
        q = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found or user unauthorized")

        if title is not None:
            post.title = title
        if body is not None:
            post.content = body
        if image_link is not None:
            post.image_link = image_link
        if tags is not None:
            post.tags = tags

        if edited_by:
            post.edited_by = edited_by.upper()

        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def like_post(self, post_id: UUID, user_id: UUID) -> Post:
        q = select(Post).where(Post.id == post_id)
        post = (await self.db.execute(q)).scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        existing = (
            await self.db.execute(
                select(PostLike).where(
                    PostLike.post_id == post_id, PostLike.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if existing:
            return post

        self.db.add(PostLike(post_id=post_id, user_id=user_id))
        post.like_count = int(post.like_count or 0) + 1
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def unlike_post(self, post_id: UUID, user_id: UUID) -> Post:
        q = select(Post).where(Post.id == post_id)
        post = (await self.db.execute(q)).scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        like_row = (
            await self.db.execute(
                select(PostLike).where(
                    PostLike.post_id == post_id, PostLike.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if not like_row:
            return post

        await self.db.delete(like_row)
        post.like_count = max(0, int(post.like_count or 0) - 1)
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def get_posts_by_username(self, username: str) -> list[Post]:
        q = (
            select(Post)
            .where(Post.user_name == username)
            .order_by(Post.created_at.desc())
        )
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def search_posts(self, query: str):
        """FTS; order by rank and likes. redis cache"""

        # 1. check cache
        cache_key = f"search:{query}"
        print("in the repo Searching cache for:", query)
        if self.cache:
            raw = await self.cache.get(cache_key)
            if raw:
                raw_s = raw.decode() if isinstance(raw, bytes) else raw
                try:
                    id_strs = json.loads(raw_s)
                    ids = [UUID(s) for s in id_strs]
                    posts = await self.get_posts_by_ids_ordered(ids)
                    if posts:
                        log.info(f"Cache hit for query: {query}")
                        return posts
                except (json.JSONDecodeError, ValueError):
                    pass

        tsquery = func.websearch_to_tsquery("english", query)
        statement = (
            select(Post)
            .where(Post.search_vector.op("@@")(tsquery))
            .order_by(
                func.ts_rank(Post.search_vector, tsquery).desc(),
                Post.like_count.desc(),
            )
        )
        res = await self.db.execute(statement)
        posts = list(res.scalars().all())
        if self.cache and posts:
            payload = json.dumps([str(p.id) for p in posts])
            await self.cache.set(cache_key, payload, ex=3600)
            log.info(f"Cache saved for query: {query} len={len(posts)}")

        return posts