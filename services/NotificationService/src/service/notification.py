
from fastapi import HTTPException, Response

from ..core.logger import logger as log
from ..lib.ws_manager import notification_ws_manager
from ..models.notifcation import Notification
from ..schema.notification import MarkAsReadRequest, SendNotificationRequest
from ..repo.notification import send_notification , mark_as_read, get_notifications_for_user
from ..lib.message_queue import get_redis

class NotificationService:
    @staticmethod
    async def send_notification(db, req: SendNotificationRequest) -> Notification:

        # 1. save in db 
        res = await send_notification(db, req)
        if not res :
            log.error("Error sending notification") 
            raise HTTPException(status_code=500, detail="Failed to send notification")

        # 2. notification payload live : 
        payload = {
            "event": "notification",
            "notification": {
                "id": str(res.id),
                "user_id": str(res.user_id),
                "publisher_id": str(res.publisher_id),
                "publisher_name": res.publisher_name,
                "user_name": res.user_name,
                "type": res.type,
                "post_id": str(res.post_id),
                "post_title": res.post_title,
                "body": res.body,
                "is_read": res.is_read,
                "created_at": res.created_at.isoformat() if res.created_at else None,
            },
        }

        await notification_ws_manager.broadcast_to_user(str(res.user_id), payload)

        # pub sub fall back : 
        try:
            redis = get_redis()
            await redis.publish("notifications", str(res.id))
        except Exception as e:
            log.warning(f"Redis publish skipped: {e}")

        log.info(f"Notification sent with ID: {res.id}")
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
        return res or []