from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...lib.db import get_db
from ..dep import get_current_user, UserContext

from ...schema.user import UserOut
from ...service.auth_admin import AdminService

router = APIRouter(tags=["admin"])


def _require_admin(actor: UserContext) -> None:
    if actor.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get(
    "/users/{role}",
    response_model=List[UserOut],
    responses={403: {"description": "Forbidden"}},
)
async def get_users(
    role: str = "all",
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    _require_admin(admin)
    svc = AdminService(db)
    return await svc.get_users(role)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserOut,
    responses={403: {"description": "Forbidden"}},
)
async def change_user_role(
    user_id: str,
    new_role: str,
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    _require_admin(admin)
    svc = AdminService(db)
    return await svc.change_user_role(user_id, new_role)


@router.delete(
    "/users/{user_id}", status_code=204, responses={403: {"description": "Forbidden"}}
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: UserContext = Depends(get_current_user),
):
    _require_admin(admin)
    svc = AdminService(db)
    return await svc.delete_user(user_id)
