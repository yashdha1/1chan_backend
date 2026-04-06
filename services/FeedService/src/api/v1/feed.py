from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...lib.db import get_db
from ...service.feed import FeedService

router = APIRouter(tags=["Feed"])

# internal ENDPOINT only accesible to the other service : 
@router.get("/generate_feed/{feed_type}")
async def generate_feed(
    feed_type: str,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = FeedService(db)
    return await svc.generate_feed(user_id, feed_type)
