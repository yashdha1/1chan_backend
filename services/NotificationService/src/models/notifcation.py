import uuid
from sqlalchemy import Column, DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..lib.db import Base
from enum import Enum

class NotificationType(Enum): 
    COMMENT = "comment"
    MENTION = "mention"
    LIKE = "like"
    DELETE = "delete" 

class Notification(Base) :
    __tablename__ = "notification"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    user_id =  Column(UUID(as_uuid=True), nullable=False)

    publisher_id = Column(UUID(as_uuid=True), nullable=False)
    publisher_name = Column(String, nullable=False) 
    user_name = Column(String, nullable=False)
    user_avatar = Column(String)
    type = Column(String, nullable=False)

    post_id = Column(UUID(as_uuid=True), nullable=False)
    post_title = Column(String, nullable=False)

    body = Column(String) # fo the comment and mentions
    is_read = Column(String, default="false")

    created_at = Column(DateTime(timezone=False), server_default=func.now()) 

# if type == like then frontend render 
# if type == comment then render the comment and the mention
# if type == mention then render the body.