from fastapi import APIRouter
from .v1.notification import router as notification_router


router = APIRouter()

router.include_router(notification_router)