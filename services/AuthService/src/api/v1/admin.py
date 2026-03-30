from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...lib.db import get_db 
from ..dep import get_current_user, UserContext

from ...models.user import Role
from ...schema.user import (
   UserOut   
)
from ...service.auth_user import AuthService

router = APIRouter(tags=["admin"])

@router.get("/users/{role}" , response_model=List[UserOut], responses={403: {"description": "Forbidden"}})
async def get_users(
    role: str = "all", 
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    if admin.role != Role.ADMIN: 
        raise   HTTPException(status_code=403, detail="Forbidden")
    svc = AuthService(db)
    return await svc.get_users(role)

@router.patch("/users/{user_id}/role", response_model=UserOut, responses={403: {"description": "Forbidden"}})
async def change_user_role(
    user_id: str,
    new_role: str,
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    if admin.role != Role.ADMIN: 
        raise HTTPException(status_code=403, detail="Forbidden")
    svc = AuthService(db)
    return await svc.change_user_role(user_id, new_role, admin)

@router.delete("/users/{user_id}", responses={403: {"description": "Forbidden"}})
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    if admin.role != Role.ADMIN: 
        raise HTTPException(status_code=403, detail="Forbidden")
    svc = AuthService(db)
    return await svc.delete_user(user_id, admin)
