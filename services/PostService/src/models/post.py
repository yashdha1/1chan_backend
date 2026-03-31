import uuid

from sqlalchemy import BigInteger, Column, DateTime, String, func, ForeignKey
from sqlalchemy_utils import TSVectorType # FTS in postgres: 
from sqlalchemy.dialects.postgresql import UUID
 

from ..lib.db import Base

class Post(Base) :
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_name = Column(String, nullable=False)
    user_avatar = Column(String)
    title = Column(String, nullable=False)
    content = Column(String)
    image_link = Column(String)
    like_count = Column(BigInteger, default=0)
    edited_by = Column(String, default="") 
    comment_count = Column(BigInteger, default=0)
    search_vector = Column(TSVectorType("title", "content"))
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())

class PostLike(Base) :
    __tablename__ = "post_likes"
    
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())