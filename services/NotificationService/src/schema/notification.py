from pydantic import BaseModel
from uuid import UUID



class SendNotificationRequest(BaseModel):
    user_id: UUID 

    publisher_id: UUID 
    publisher_name: str
    user_name: str  
    type: str 
    post_id: UUID 
    post_title: str
    body: str | None = None

class MarkAsReadRequest(BaseModel):
    notification_id: UUID