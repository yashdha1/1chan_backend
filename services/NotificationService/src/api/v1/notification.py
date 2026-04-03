from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from ...lib.db import get_db
from ...schema.notification import SendNotificationRequest, MarkAsReadRequest
from ...service.notification import NotificationService 
from ..dep import get_current_user



router = APIRouter()


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await NotificationService.send_notification(db, request)
    return res

@router.post("/mark")
async def mark_as_read(
    request: MarkAsReadRequest,
    db: AsyncSession = Depends(get_db), 
    user = Depends(get_current_user)
):
    res = await NotificationService.mark_as_read(db, request, user.id)
    return res

@router.post("/activity/{offset}")
async def get_notifications_for_user(
    offset: int,
    db: AsyncSession = Depends(get_db), 
    user = Depends(get_current_user)
) : 
    if not user: 
        raise HTTPException(status_code=401, detail="Unauthorized")
    res = await NotificationService.get_notifications_for_user(db, user.id, offset)
    return res 