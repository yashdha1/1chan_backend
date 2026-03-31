from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.time import timer 

from ..models.post import Post
from fastapi import HTTPException
from ..core.logger import logger as log 

class PostRepository:
    def __init__(self, db, cache=None):
        self.db = db
        self.cache = cache

    async def create_post(self, post_data):
        new_post = Post(**post_data)
        self.db.add(new_post)
        await self.db.commit()
        await self.db.refresh(new_post)
        return new_post

    async def get_post_by_id(self, post_id):
        q = select(Post).where(Post.id == UUID(post_id))
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        return post
    
    async def delete_post(self, post_id, user_id): 
        q = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        res = await self.db.execute(q)
        post = res.scalar_one_or_none()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
        await self.db.delete(post)
        await self.db.commit()
        return True
    
    async def patch_post(self, post_id, user_id, title: str | None = None, body: str | None = None, image_link: str | None = None, edited_by: str = "") :
        q = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        res = await self.db.execute(q)
        post = res.scalar_one_or_none() # get the post object
        if not post:
            raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
        
        if title:
            post.title = title
        if body :
            post.body = body
        if image_link :
            post.image_link = image_link
        
        if edited_by:
            post.edited_by = edited_by.upper() # either by the ADMIN or the MODERARTOR.

        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return post
    
    # @lru_cache(maxsize=128) 

    @timer
    async def search_posts(self, query) :
        """FTS in the sause, for now having the return type by the popularity of the likes.
            adding the limit of pagination in the future.
        """
        # 1. check for the cache first : 
        if self.cache:
            cached_result = await self.cache.get(f"search:{query}")
            if cached_result: 
                log.info(f"Cache hit for query: {query}")
                return cached_result
            
        # execute the search query in the database
        # 2. Execute the query noramally :
        statement = (
                select(Post)
                .where(Post.search_vector.match(query, postgresql_regconfig="english"))
                .order_by(func.ts_rank(Post.search_vector, func.plainto_tsquery(query)), Post.like_count.desc())
        )
        res = await self.db.execute(statement)
        posts = res.scalars().all()
        
        # 3. store in the cache for the further
        if self.cache :
            log.info(f"Cache saved for query: {query} of the len: {len(posts)}")
            self.cache.set(f"search:{query}", posts, ex=3600) 
        
        return posts
    
    # TODO : add a batch post fetching feature: for the results of the feed wali shit