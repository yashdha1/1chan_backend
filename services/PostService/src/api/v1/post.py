from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..dep import UserContext, get_current_user
from ...lib.db import get_db
from ...lib.redis import get_redis
from ...models.post import Post
from ...schema.posts.posts import (
    PatchPostRequest,
    PostRequest,
    PostResponse,
    SearchPostItem,
    SearchPostsResponse,
    SearchPostRequest,
)
from ...service.post import PostService

router = APIRouter(tags=["Posts"])


def _post_res(post: Post) -> PostResponse:
    return PostResponse(
        post_id=post.id,
        user_id=post.user_id,
        user_name=post.user_name,
        user_avatar=post.user_avatar,
        body=post.content or "",
        title=post.title,
        image_link=post.image_link,
        like_count=int(post.like_count or 0),
        comment_count=int(post.comment_count or 0),
    )


def _create_payload(req: PostRequest, user: UserContext) -> dict:
    return {
        "user_id": user.id,
        "user_name": user.uname,
        "user_avatar": user.avatar or None,
        "title": req.title,
        "content": req.body,
        "image_link": req.image_link,
    }


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    post = await svc.create_post(_create_payload(body, user))
    return _post_res(post)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
): 
    svc = PostService(db, response, r)
    post = await svc.get_post_by_id(str(post_id))
    return _post_res(post)


@router.patch("/{post_id}", response_model=PostResponse)
async def patch_post(
    post_id: UUID,
    body: PatchPostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    post = await svc.patch_post(
        post_id,
        user.id,
        title=body.title,
        body=body.body,
        image_link=body.image_link,
        edited_by=body.edited_by,
    )
    return _post_res(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    await svc.delete_post(user.id, post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/search", response_model=SearchPostsResponse)
async def search_posts(
    body: SearchPostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = PostService(db, response, r)
    posts = await svc.search_posts(body.query)
    items = [
        SearchPostItem(
            post_id=p.id,
            title=p.title,
            body=p.content or "",
            offset=i,
        )
        for i, p in enumerate(posts)
    ]
    return SearchPostsResponse(items=items)