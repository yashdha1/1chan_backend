from sqlalchemy import select
from fastapi import HTTPException, Response 
 
from ..models.notifcation import Notification

async def send_notification(db, req):
    try :
        notification = Notification(**req.dict())
        print(f"Notification: {notification}")
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification 
    except Exception:
        raise HTTPException(status_code=500, detail="DB error sending notification.")
    
async def mark_as_read(db, req, user_id):
    stmt = select(Notification).where(Notification.id == req.notification_id and Notification.user_id == user_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = "true"
    await db.commit()
    return Response(content="Notification marked as read", status_code=200)

async def get_notifications_for_user(db, user_id, offset):
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(15)
        .offset(offset)
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return notifications