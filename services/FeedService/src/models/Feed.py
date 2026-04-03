from ..lib.db import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Float

class tags(Base): 
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)
    post_count = Column(Integer, default=0)   # for popularity

class post_tags(Base):
    __tablename__ = "post_tags"

    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)

class tag_weight(Base):
    __tablename__ = "tag_weight"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    weight = Column(Float, default=0)
    updated_at = Column(DateTime, default=func.now())

class post_viewed(Base): 
    __tablename__ = "post_viewed"

    post_id = Column(Integer, ForeignKey("posts.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    viewed_at = Column(DateTime, default=func.now())