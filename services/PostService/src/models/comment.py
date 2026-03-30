import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ..lib.db import Base

class Comment(Base) :
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    post_id = Column(UUID(as_uuid=True), ForeignKey("contents.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"))
    user_id =  Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String, nullable=False)
    user_avatar = Column(String)
    body = Column(String, nullable=False)
    like_count = Column(BigInteger, default=0)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

class CommentLike(Base) :
    __tablename__ = "comment_likes"

    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())