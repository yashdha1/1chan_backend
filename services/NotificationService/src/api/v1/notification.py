from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import HTTPException

from ...lib.db import get_db
from ...lib.ws_manager import notification_ws_manager
from ...schema.notification import SendNotificationRequest, MarkAsReadRequest
from ...service.notification import NotificationService 
from ..dep import get_current_user, get_current_user_ws



router = APIRouter()


@router.websocket("/ws/live")
async def notifications_live_socket(websocket: WebSocket):
    try:
        user = get_current_user_ws(websocket)
    except HTTPException:
        await websocket.close(code=4401)
        return

    uid = str(user.id)
    await notification_ws_manager.connect(websocket, uid)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_ws_manager.disconnect(websocket, uid)

# Send and deliver notifications via websocket manager.
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
    res = await NotificationService.get_notifications_for_user(db, user.id, offset)
    return res 