from fastapi import APIRouter

from .v1.comment import router as comment_router
from .v1.post import router as post_router

router = APIRouter()

router.include_router(post_router)
router.include_router(comment_router, prefix="/comments")
