from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..dep import UserContext, get_current_user
from ...lib.db import get_db
from ...lib.redis import get_redis
from ...models.comment import Comment
from ...schema.comments.comment import (
    CommentLikeRequest,
    CommentPostRequest,
    CommentResponse,
    CommentUnlikeRequest,
)
from ...service.comment import CommentService
from .post_manager import manager

router = APIRouter(tags=["Comments"])


def _comment_res(c: Comment) -> CommentResponse:
    return CommentResponse(
        comment_id=c.id,
        post_id=c.post_id,
        parent_id=c.parent_id,
        user_id=c.user_id,
        user_name=c.user_name,
        user_avatar=c.user_avatar,
        body=c.body,
        like_count=int(c.like_count or 0),
        created_at=c.created_at.isoformat() if c.created_at else None,
    )


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    body: CommentPostRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = CommentService(db, response, r)
    comment = await svc.create_comment(
        post_id=body.post_id,
        parent_id=body.parent_id,
        user_id=user.id,
        user_name=user.uname,
        user_avatar=user.avatar or None,
        body=body.body,
    )
    res = _comment_res(comment)

    await manager.broadcast_post(
        str(body.post_id),
        {"event": "comment_update", "comment": res.model_dump(mode="json")},
    )
    if body.parent_id is not None:
        await manager.broadcast_thread(
            str(body.post_id),
            str(body.parent_id),
            {"event": "new_reply", "comment": res.model_dump(mode="json")},
        )

    return res


@router.get("/{post_id}", response_model=list[CommentResponse])
async def list_comments_for_post(
    post_id: UUID,
    response: Response,
    offset: int = Query(default=0, ge=0),
    parent_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    """gets comments for the specified post. DEFAULT -> DESC order by like"""
    print("in the api endpoint")
    svc = CommentService(db, response, r)
    comments = await svc.list_for_post(post_id, offset, parent_id)
    return [_comment_res(c) for c in comments]


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = CommentService(db, response, r)
    await svc.delete_comment(comment_id, user.id, user.role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/like", response_model=CommentResponse)
async def like_comment(
    body: CommentLikeRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = CommentService(db, response, r)
    comment = await svc.like_comment(body.comment_id, user.id)
    return _comment_res(comment)


@router.post("/unlike", response_model=CommentResponse)
async def unlike_comment(
    body: CommentUnlikeRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = CommentService(db, response, r)
    comment = await svc.unlike_comment(body.comment_id, user.id)
    return _comment_res(comment)
