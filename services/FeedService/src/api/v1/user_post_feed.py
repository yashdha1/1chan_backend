from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...lib.db import get_db
from ...schema.feed import (
    PostsViewed,
    UpdatePostTags,
    PostTagAdd,
    TagInsert
)
from ...service.feed import FeedService
from ..dep import get_current_user, UserContext

router = APIRouter(prefix="/operation", tags=["post_feeds"])


@router.post("/viewed_posts")
async def posts_view(
    body: PostsViewed,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedService(db)
    await svc.mark_viewed(user.id, [p.post_id for p in body.posts])
    return {"ok": True}


@router.post("/update_weights")
async def update_weights(
    body: UpdatePostTags,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedService(db)
    await svc.update_weights(user.id, body.tags, body.op)
    return {"ok": True}

@router.post("/add_tag")
async def tag_add(
    body: TagInsert,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    svc = FeedService(db)
    await svc.add_tag(body.tag)
    return {"ok": True}

# this is done by the messaging queue: by the postal service.
@router.post("/post_add_tags")
async def post_add_tags(
    body: PostTagAdd,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedService(db)
    await svc.add_post_tags(body.post_id, body.tags)
    return {"ok": True}


@router.get("/get_tags")
async def get_tags(db: AsyncSession = Depends(get_db)):
    svc = FeedService(db)
    return await svc.get_tags()
