from uuid import UUID

from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logger import logger as log
from ..repo.post import PostRepository
from .AsyncClient import AsyncClient
from ..lib.publish import publish_notification

class PostService:
    def __init__(self, db: AsyncSession, response: Response, r=None) -> None:
        self.db = db
        self.cache = r
        self.post_repo = PostRepository(self.db, self.cache)

    async def create_post(self, post_data: dict):
        try:
            res = await self.post_repo.create_post(post_data)
            log.info(f"Post created with ID: {res.id}")
            await AsyncClient.map_post_to_feed(res)
            log.info(f"Post-to-feed mapping updated for post ID via the interservice calls: {res.id}")
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

    async def delete_post(self, uid: UUID | None, post_id: UUID):
        try:
            can_delete_any = uid is None
            res = await self.post_repo.delete_post(post_id, uid, can_delete_any=can_delete_any)
            if not res:
                raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
            log.info(f"Post deleted with ID: {post_id}")
        except HTTPException as he:
            log.error(f"Error deleting post: {he.detail}")
            raise he
        except Exception as e:
            log.error(f"Error deleting post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def delete_post_high(self, post_id: UUID):
        """This is a high level delete which will be called by the feed service when a post is deleted, it will take care of deleting the post from the feed as well."""
        try:
            res = await self.post_repo.delete_post_high(post_id)
            if not res:
                raise HTTPException(status_code=404, detail="Post not found or user unauthorized")
            log.info(f"Post deleted with ID: {post_id} via high level delete")
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
        tags: str | None = None,
    ):
        """patch the post"""
        try:
            res = await self.post_repo.patch_post(
                post_id, uid, title, body, image_link, edited_by, tags
            )
            log.info(f"Post patched with ID: {post_id}")
            return res
        except HTTPException as he:
            log.error(f"Error patching post: {he.detail}")
            raise he
        except Exception as e:
            log.error(f"Error patching post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def like_post(self, post_id: UUID, user_id: UUID, user_name):
        try:
            await self.post_repo.like_post(post_id, user_id)
            log.info(f"Post liked: {post_id} by {user_id}")
            post_details = await self.post_repo.get_post_by_id(post_id)

             # send notification to the posts publisher: 
            if post_details and post_details.user_id != user_id : 
                # await AsyncClient.send_notification({
                #     "user_id": str(post_details.user_id),        #kisko bheja 
                #     "publisher_id": str(user_id),   #kisne bheja
                #     "publisher_name": str(user_name),    # bhejne wale ka naam    
                #     "user_name": str(user_name),  # for like notification, the user_name and publisher_name will be same, but for comment they will be different.
                #     "type": "like",                             
                #     "post_id": str(post_id), # konsa post  
                #     "post_title": post_details.title  # post ka title
                # })
                await publish_notification(
                    user_id=str(post_details.user_id),        #kisko bheja
                    publisher_id=str(user_id),   #kisne bheja
                    publisher_name=str(user_name),    # bhejne wale ka naam
                    user_name=str(user_name),  # for like notification, the user_name and publisher_name will be same, but for comment they will be different.
                    type="like",                             
                    post_id=str(post_id), # konsa post
                    post_title=post_details.title  # post ka title
                )

                log.info(f"Notification sent for like on post ID: {post_id} to user ID: {post_details.user_id}")
            return post_details
 
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
            
            print("Searching for:", query)
            res = await self.post_repo.search_posts(query)
            log.info(f"Search completed for query: {query} with {len(res)} results")
            return res
        except Exception :
            log.exception(f"Error searching posts for query: {query}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    async def get_posts_by_username(self, username: str):
        try:
            return await self.post_repo.get_posts_by_username(username)
        except Exception:
            log.exception(f"Error fetching posts for user: {username}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def get_post_liked_by(self, post_id: UUID): 
        try : 
            return await self.post_repo.get_post_liked_by(post_id)
        except Exception:
            log.exception(f"Error fetching liked by for post: {post_id}")
            raise HTTPException(status_code=500, detail="Internal Server Error") 

    async def build_feed(self, user_id: UUID, feed_type: str):
        try:
            print(f"Building feed for user ID {user_id} with feed type {feed_type}")
            return await self.post_repo.build_feed(user_id, feed_type)
        except Exception:
            log.exception(f"Error building feed for user: {user_id}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def patch_self_post(self, post_id: UUID, uid: UUID, body: str | None = None, edited_by: str = ""):
        try:
            res = await self.post_repo.patch_self_post(post_id, uid, body, edited_by)
            log.info(f"Post patched with ID: {post_id} by user ID: {uid}")
            return res
        except HTTPException as he:
            log.error(f"Error patching post: {he.detail}")
            raise he
        except Exception as e:
            log.error(f"Error patching post: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")