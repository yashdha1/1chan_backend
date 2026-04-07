from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from fastapi import HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.dep import UserContext

from ..core.config import settings
from ..core.logger import logger as log
from ..models.user import User
from ..schema.user import (
    UserLoginRequest,
    UserLoginResponse,
    UserOut,
    UserRegistrationRequest,
    ProfileUpdateRequest,
)
from ..lib.publish import publish_user_updated


def _role_claim(role) -> str:
    return role.value if hasattr(role, "value") else str(role)


def _verify_actor(actor: UserContext, target: User) -> None:
    """verify id"""
    if actor.id == target.id:
        return
    if actor.role == "admin":
        return
    raise HTTPException(
        status_code=403,
        detail="You can only update or delete your own profile",
    )


class AuthService:
    def __init__(self, db: AsyncSession, response: Response, r=None) -> None:
        self.db = db
        self.redis = r
        self.res = response

    async def create_user(self, data: UserRegistrationRequest) -> UserLoginResponse:
        """
        Create a new user
        Args:
            data: UserRegistrationRequest
        Returns:
            UserLoginResponse
        """
        query = select(User).where(User.username == data.username)
        result = await self.db.execute(query)
        already_exists = result.scalar_one_or_none()

        if already_exists:
            raise HTTPException(status_code=409, detail="User already exists")

        hashed_password = bcrypt.hashpw(
            data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        new_user = User(
            id = data.id,
            username=data.username,
            password=hashed_password,
            bio=data.bio,
            avatar=data.avatar,
            role=data.role,
        )
        print("new user : ", new_user) 

        try:
            self.db.add(new_user)
            await self.db.commit()
            await self.db.refresh(new_user)
        except Exception:
            await self.db.rollback()
            log.error(f"User {data.username} registration failed.")
            raise HTTPException(status_code=500, detail="User registration failed.")

        access_token, refresh_token = self._generate_token(new_user)

        self.res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        self.res.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        await self.redis.set(
            f"refresh_token:{new_user.id}",
            refresh_token,
            ex=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        log.info(f"User {data.username} registered.")
        return UserLoginResponse(access_token=access_token, refresh_token=refresh_token)

    async def login_user(self, data: UserLoginRequest) -> UserLoginResponse:
        query = select(User).where(User.username == data.username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not bcrypt.checkpw(
            data.password.encode("utf-8"), user.password.encode("utf-8")
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token, refresh_token = self._generate_token(user)

        self.res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        self.res.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        await self.redis.set(
            f"refresh_token:{user.id}",
            refresh_token,
            ex=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        log.info(f"User {data.username} logged in.")

        return UserLoginResponse(access_token=access_token, refresh_token=refresh_token)

    async def logout_user(self, actor: UserContext, refresh_token: str) -> None:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        uid = payload.get("id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token")

        if UUID(uid) != actor.id:
            raise HTTPException(
                status_code=403, detail="Cannot log out another session"
            )

        stored_token = await self.redis.get(f"refresh_token:{uid}")
        stored_str = (
            stored_token.decode("utf-8")
            if isinstance(stored_token, (bytes, bytearray))
            else stored_token
        )
        if not stored_str or stored_str != refresh_token:
            raise HTTPException(status_code=401, detail="Token already revoked")

        await self.redis.delete(f"refresh_token:{uid}")
        self.res.delete_cookie(key="access_token")
        self.res.delete_cookie(key="refresh_token")
        log.info(f"User {uid} logged out.")

    async def get_profile(self, username: str) -> UserOut:
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        return UserOut(
            id=user.id,
            username=user.username,
            bio=user.bio,
            avatar=user.avatar,
            role=role_val,
            is_active=user.is_active,
        )

    async def refresh(self, refresh_token: str) -> UserLoginResponse:
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        uid = payload.get("id")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stored = await self.redis.get(f"refresh_token:{uid}")
        stored_str = (
            stored.decode("utf-8") if isinstance(stored, (bytes, bytearray)) else stored
        )
        if not stored_str or stored_str != refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        result = await self.db.execute(select(User).where(User.id == UUID(uid)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token, refresh_token = self._generate_token(user)
        self.res.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        self.res.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        await self.redis.set(
            f"refresh_token:{user.id}",
            refresh_token,
            ex=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
        log.info(f"User {user.username} refreshed.")
        return UserLoginResponse(access_token=access_token, refresh_token=refresh_token)

    async def update_profile(
        self, username: str, body: ProfileUpdateRequest, user: UserContext
    ) -> UserOut:
        try:
            query = select(User).where(User.id == user.id)
            result = await self.db.execute(query)
            usr = result.scalar_one_or_none()

            if not usr:
                raise HTTPException(status_code=404, detail="User not found")
            _verify_actor(user, usr)
            if body.username != usr.username:
                exists_query = select(User).where(User.username == body.username)
                exists_result = await self.db.execute(exists_query)
                exists_user = exists_result.scalar_one_or_none()
                if exists_user and exists_user.id != usr.id:
                    raise HTTPException(status_code=409, detail="Username already exists")

            usr.username = body.username
            usr.bio = body.bio
            usr.avatar = body.avatar

            await self.db.commit()
            await self.db.refresh(usr)
            log.info(f"User {username} updated their profile.")

            # publish the event
            await publish_user_updated(str(usr.id), usr.username, usr.avatar or "")
            log.info(f"Published user profile update event for user {username}.")
            return UserOut(
                id=usr.id,
                username=usr.username,
                bio=usr.bio,
                avatar=usr.avatar,
                role=usr.role.value if hasattr(usr.role, "value") else str(usr.role),
                is_active=usr.is_active,
            )
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            log.error("error updating the profile fields for the user.")
            raise HTTPException(status_code=500, detail="Failed to update profile.")

    async def delete_profile(self, user: UserContext) -> None:
        try:
            query = select(User).where(User.id == user.id)
            res = await self.db.execute(query)
            usr = res.scalar_one_or_none()
            if not usr:
                raise HTTPException(status_code=404, detail="User not found")
            _verify_actor(user, usr)
            await self.db.delete(usr)
            await self.db.commit()
            log.info(f"User {user.username} deleted their profile.")
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            log.error("error deleting the user profile.")
            raise HTTPException(status_code=500, detail="Failed to delete profile.")
    
    async def delete_profile_by_admin(self, id: UUID) -> None:
        try:
            query = select(User).where(User.id == id)
            res = await self.db.execute(query)
            usr = res.scalar_one_or_none()
            if not usr:
                raise HTTPException(status_code=404, detail="User not found")
            await self.db.delete(usr)
            await self.db.commit()
            log.info(f"User {id} deleted by admin.")
        except HTTPException:
            raise
        except Exception:
            await self.db.rollback()
            log.error("error deleting the user profile by admin.")
            raise HTTPException(status_code=500, detail="Failed to delete profile.")

    # helper
    def _generate_token(self, data: User) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        access_exp = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_exp = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        role = _role_claim(data.role)
        access_payload = {
            "id": str(data.id),
            "username": data.username,
            "role": role,
            "iss": "1chan-server",
            "avatar": data.avatar or "",
            "iat": int(now.timestamp()),
            "exp": int(access_exp.timestamp()),
        }
        refresh_payload = {
            "id": str(data.id),
            "username": data.username,
            "role": role,
            "iss": "1chan-server",
            "iat": int(now.timestamp()),
            "exp": int(refresh_exp.timestamp()),
        }
        try:
            access_token = jwt.encode(
                access_payload,
                settings.JWT_PRIVATE_KEY,
                algorithm=settings.JWT_ALGORITHM,
            )
            refresh_token = jwt.encode(
                refresh_payload,
                settings.JWT_PRIVATE_KEY,
                algorithm=settings.JWT_ALGORITHM,
            )
        except jwt.PyJWTError as exc:
            log.exception("JWT encode failed")
            raise HTTPException(
                status_code=500,
                detail=(
                    "JWT signing failed. For RS256, set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY "
                    "to RSA PEM (or JWT_*_FILE paths to PEM files)."
                ),
            ) from exc
        return (access_token, refresh_token)
