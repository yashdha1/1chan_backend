from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio.client import Redis

from ...lib.db import get_db
from ...lib.redis import get_redis

from ...schema.user import (
    Profile,
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
)
from ...service.auth_user import AuthService


router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserLoginResponse)
async def register(
    body: UserRegistrationRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = AuthService(db, response, r)
    return await svc.create_user(body)


@router.post("/login", response_model=UserLoginResponse)
async def login(
    body: UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    svc = AuthService(db, response, r)
    return await svc.login_user(body)


@router.post("/refresh", response_model=UserLoginResponse)
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    r: Redis = Depends(get_redis),
):
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    svc = AuthService(db, response, r)
    return await svc.refresh(refresh)


@router.get("/profile/{username}", response_model=Profile)
async def get_profile(
    username: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db, response)
    user = await svc.get_profile(username)
    return Profile(user=user)


# TODO: Formatting  # noqa
# TODO: stucture    # noqa
