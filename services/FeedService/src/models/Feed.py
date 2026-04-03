from ..lib.db import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func 
from sqlalchemy.dialects.postgresql import JSONB

class tags(Base): 
    __tablename__ = "tags"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String, nullable=False, unique=True)
    post_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

class post_tags(Base):
    __tablename__ = "post_tags"

    post_id    = Column(Integer, primary_key=True)
    tag_id     = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

class user_tag_profile(Base):
    __tablename__ = "user_tag_profile"

    user_id    = Column(Integer, primary_key=True)
    weights    = Column(JSONB, default={})    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class post_viewed(Base):
    __tablename__ = "post_viewed"
    user_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, primary_key=True)
    seen_at = Column(DateTime, default=func.now())