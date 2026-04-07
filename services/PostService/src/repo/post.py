import json
from uuid import UUID

from sqlalchemy import select, func, delete
# from sqlalchemy.ext.asyncio import AsyncSession # noqa F401

from ..models.comment import Comment, CommentLike
from ..models.post import Post, PostLike
from fastapi import HTTPException
from ..core.logger import logger as log
from ..service.AsyncClient import AsyncClient


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

    async def delete_post(self, post_id, user_id: UUID | None = None, can_delete_any: bool = False): 
        q = select(Post).where(Post.id == post_id)
        if not can_delete_any:
            q = q.where(Post.user_id == user_id)
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found or user unauthorized")

        comment_ids_query = select(Comment.id).where(Comment.post_id == post_id)
        comment_ids_res = await self.db.execute(comment_ids_query)
        comment_ids = list(comment_ids_res.scalars().all())

        if comment_ids:
            await self.db.execute(
                delete(CommentLike).where(CommentLike.comment_id.in_(comment_ids)) 
            )
            await self.db.execute(delete(Comment).where(Comment.post_id == post_id))

        await self.db.execute(delete(PostLike).where(PostLike.post_id == post_id))
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
        
        # 2. SEARCH q
        tsquery = func.websearch_to_tsquery("english", query)
        statement = (
            select(Post)
            .where(Post.search_vector.op("@@")(tsquery))
            .order_by(
                func.ts_rank(Post.search_vector, tsquery).desc(),
                Post.like_count.desc(),
            )
            .limit(10)
        )
        res = await self.db.execute(statement)
        posts = list(res.scalars().all())

        # 3. cache hit
        if self.cache and posts:
            payload = json.dumps([str(p.id) for p in posts])
            await self.cache.set(cache_key, payload, ex=3600)
            log.info(f"Cache saved for query: {query} len={len(posts)}")

        return posts
    
    async def get_post_liked_by(self, post_id: UUID) -> list[str]:
        """fetch the list of user who like the post with ID post_id"""
        q = (
            select(Post.user_name)
            .join(PostLike, PostLike.user_id == Post.user_id)
            .where(PostLike.post_id == post_id)
            .distinct()
        )
        res = await self.db.execute(q)
        users = [user_name for user_name in res.scalars().all() if user_name]
        return users
    
    async def build_feed(self, user_id: UUID, feed_type) -> list[Post]:
        try:
            feed = await AsyncClient.get_feed_for_user(str(user_id), feed_type)
            if not feed:
                log.info(f"No feed data received for user ID {user_id} and feed type {feed_type}")
                return []
            raw_post_ids = feed.get("post_ids", [])
            post_ids = [UUID(str(post_id)) for post_id in raw_post_ids]
            log.info(
                f"Received feed data for user ID {user_id} and feed type {feed_type}: {raw_post_ids}"
            )

            posts = await self.get_posts_by_ids_ordered(post_ids)
            log.info(f"Build feed repo: {feed_type} with {len(post_ids)} post IDs")

            # TODO: case where the ids are missign is rare and only exists in the development
            # due to the seeding of the database. Monitor once deployed. 
            
            log.info(f"Successfully built feed for user ID {user_id} and feed type {feed_type} with {len(posts)} posts")
            return posts
        except Exception as e:
            log.error(f"Error building feed for user ID {user_id} and feed type {feed_type}: {e}")
            raise HTTPException(status_code=500, detail="Failed to build feed")