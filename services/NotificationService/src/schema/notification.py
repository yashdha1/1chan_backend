from pydantic import BaseModel
from uuid import UUID



class SendNotificationRequest(BaseModel):
    user_id: UUID 

    publisher_id: UUID 
    publisher_name: str
    user_name: str 
    user_avatar: str  
    type: str 
    post_id: UUID 
    post_title: str 
    body: str | None = None # can be a like wala comment

class MarkAsReadRequest(BaseModel):
    notification_id: UUID