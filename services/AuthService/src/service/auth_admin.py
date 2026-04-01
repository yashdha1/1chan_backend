from uuid import UUID
 
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
 
from ..core.logger import logger as log
from ..models.user import User, Role


class AdminService: 
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_users(self, role: str):
        try:
            if role == "all":
                stmt = select(User).where(User.role.notin_([Role.ADMIN, Role.MOD]))
            elif role == "mod":
                stmt = select(User).where(User.role == Role.MOD)
            elif role == "user":
                stmt = select(User).where(User.role == Role.USER)
            else:
                raise HTTPException(status_code=400, detail="Invalid role filter")
            
            result = await self.db.execute(stmt)
            users = result.scalars().all()
            return users
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error fetching admin users: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def change_user_role(self, user_id: str, new_role: str):
        try: 
            stmt = select(User).where(User.id == UUID(user_id))
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if new_role not in ["user", "mod"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            
            user.role = Role(new_role)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except HTTPException as he:
            raise he
        except Exception as e:
            log.error(f"Error changing user role: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")
    
    async def delete_user(self, delete_user_id: str):
        try: 
            q = select(User).where(User.id == UUID(delete_user_id))
            result = await self.db.execute(q)
            user = result.scalar_one_or_none() 
            if not user :
                raise HTTPException(status_code=404, detail="User not found")
            await self.db.delete(user)
            log.info(f"Deleted user with id: {delete_user_id} by the admin himself")
            await self.db.commit()
        except HTTPException as he:
            raise he
        except Exception as e:
            log.error(f"Error deleting user: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")