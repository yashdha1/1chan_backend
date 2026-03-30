from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio.client import Redis


from ...schema.user import Profile, ProfileUpdateRequest
from ...service.auth_user import AuthService

from ...lib.db import get_db
from ...lib.redis import get_redis 

from ..dep import get_current_user, get_current_user_flexible, UserContext

router = APIRouter(tags=["auth"])

@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    user: UserContext = Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    svc = AuthService(db, response, r)
    await svc.logout_user(user, refresh)
    
@router.patch("/profile/{username}", response_model=Profile)
async def update_profile(
    username: str,
    body: ProfileUpdateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = AuthService(db, response, r)
    updated = await svc.update_profile(username, body, user)
    return Profile(user=updated)

@router.delete("/profile/{username}", status_code=204)
async def delete_profile(
    username: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
    user: UserContext = Depends(get_current_user),
):
    svc = AuthService(db, response, r)
    return await svc.delete_profile(username, user)


# TODO: Password reset. # noqa 