import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID

from ..lib.db import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    MOD = "mod"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    bio = Column(String)
    avatar = Column(String)
    role = Column(SAEnum(Role), default=Role.USER)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())   