from fastapi import APIRouter
from .v1.auth import router as free_auth_router 
from .v1.users import router as auth_router
from .v1.admin import router as admin_router

router = APIRouter()

router.include_router(free_auth_router)
router.include_router(auth_router)
router.include_router(admin_router)
