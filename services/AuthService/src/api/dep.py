from uuid import UUID

from fastapi import HTTPException, Request
import jwt
from pydantic import BaseModel

from ..core.config import settings


class UserContext(BaseModel):
    id: UUID
    role: str
    uname: str
    avatar: str


def _decode_access_token(token: str) -> UserContext:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid = payload.get("id")
    uname = payload.get("username")
    role = payload.get("role")

    if not uid or not uname or not role:
        raise HTTPException(status_code=401, detail="Invalid token")

    return UserContext(
        id=UUID(uid),
        role=role,
        uname=uname,
        avatar=payload.get("avatar") or "",
    )


def get_current_user(request: Request) -> UserContext:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return _decode_access_token(token)
