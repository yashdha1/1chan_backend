from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...lib.db import get_db
from ...schema.feed import (
    GenerateFeed,
)
from ...service.feed import FeedService
from ..dep import get_current_user, UserContext

router = APIRouter(tags=["Feed"])

@router.get("/generate_feed")
async def generate_feed(
    body: GenerateFeed,
    user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = FeedService(db)
    return await svc.generate_feed(user.id, body.feed_type)
