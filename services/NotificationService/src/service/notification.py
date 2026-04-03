
from fastapi import HTTPException, Response

from ..core.logger import logger as log
from ..models.notifcation import Notification
from ..schema.notification import MarkAsReadRequest, SendNotificationRequest
from ..repo.notification import send_notification , mark_as_read, get_notifications_for_user

class NotificationService:
    @staticmethod
    async def send_notification(db, req: SendNotificationRequest) -> Notification:
        res = await send_notification(db, req)
        if not res :
            log.error("Error sending notification") 
            raise HTTPException(status_code=500, detail="Failed to send notification")
        return res

    
    @staticmethod
    async def mark_as_read(db, req: MarkAsReadRequest, user_id) -> Response:  
        res =  await mark_as_read(db, req, user_id)
        if not res :
            log.error("Error marking notification as read") 
            raise HTTPException(status_code=500, detail="Failed to mark notification as read")
        return res 
    
    @staticmethod
    async def get_notifications_for_user(db, user_id, offset) -> list[Notification]:
        res = await get_notifications_for_user(db, user_id, offset)
        if not res :
            log.error("Error getting notifications for user") 
            raise HTTPException(status_code=500, detail="Failed to get notifications for user")
        return res