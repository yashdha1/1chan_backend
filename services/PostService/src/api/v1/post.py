from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..dep import UserContext, get_current_user
from ...lib.db import get_db
from ...lib.redis import get_redis
from ...models.post import Post
from ...schema.posts.posts import (
    LikedByResponse,
    PatchPostRequest,
    CreatePostRequest,
    PostResponse,
    SearchPostItem,
    SearchPostsResponse,
    SearchPostRequest,
    FeedPostResponse
)
from ...service.post import PostService
from .post_manager import manager

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
        tags=[t for t in (post.tags or "").split(",") if t],
    )


def _create_payload(req: CreatePostRequest, user: UserContext) -> dict:
    return {
        "user_id": user.id,
        "user_name": user.uname,
        "user_avatar": user.avatar or None,
        "title": req.title,
        "content": req.body,
        "image_link": req.image_link,
        "tags": ",".join(req.tags),  # save as a string 
    }


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: CreatePostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    post = await svc.create_post(_create_payload(body, user))
    return _post_res(post)


@router.get("/user/{username}", response_model=list[PostResponse])
async def get_posts_by_username(
    username: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = PostService(db, response, r)
    posts = await svc.get_posts_by_username(username)
    return [_post_res(p) for p in posts]


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
        tags=",".join(body.tags) if body.tags is not None else None,
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
    requester_id = None if (user.role or "").lower() in {"admin", "mod"} else user.id
    await svc.delete_post(requester_id, post_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{post_id}/like", response_model=PostResponse)
async def like_post(
    post_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    post = await svc.like_post(post_id, user.id, user.uname)
    await manager.broadcast_post(
        str(post_id), {"event": "like_update", "like_count": int(post.like_count or 0)}
    )
    return _post_res(post)


@router.post("/{post_id}/unlike", response_model=PostResponse)
async def unlike_post(
    post_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    post = await svc.unlike_post(post_id, user.id)
    await manager.broadcast_post(
        str(post_id), {"event": "like_update", "like_count": int(post.like_count or 0)}
    )
    return _post_res(post)


@router.post("/search", response_model=SearchPostsResponse)
async def search_posts(
    body: SearchPostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = PostService(db, response, r)
    print("Searching for:", body.query)
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

@router.get("/{post_id}/liked_by", response_model=LikedByResponse)
async def get_post_liked_by(
    post_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = PostService(db, response, r)
    users = await svc.get_post_liked_by(post_id)
    return LikedByResponse(users=users)

@router.get("/build_feed/{feed_type}", response_model=FeedPostResponse) 
async def build_feed(
    feed_type: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = PostService(db, response, r)
    if feed_type not in ("suggested", "latest", "community"): 
        return Response(status_code=status.HTTP_400_BAD_REQUEST, content="Invalid feed type")
    posts = await svc.build_feed(user.id, feed_type) 

    return FeedPostResponse(posts=[_post_res(p) for p in posts])