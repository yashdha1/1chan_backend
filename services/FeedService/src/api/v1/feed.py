from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Feed"])

# @router.get("/generate-feed")
# async def get_feed(user: User = Depends(get_current_user)):
#     return {"message": "Feed generated successfully"}