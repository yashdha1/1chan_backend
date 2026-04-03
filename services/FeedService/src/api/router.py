from fastapi import APIRouter

from .v1.feed import router as feed_router
from .v1.user_post_feed import router as user_post_feed_router

router = APIRouter(prefix="/feed")

router.include_router(feed_router)
router.include_router(user_post_feed_router)
