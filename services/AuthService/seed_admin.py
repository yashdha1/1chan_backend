import asyncio
import os

import bcrypt
from sqlalchemy import select

from src.lib.db import AsyncSessionLocal, Base, engine
from src.models.user import User, Role


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "onechan_admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234567890")
ADMIN_BIO = os.getenv("ADMIN_BIO", "Super admin account")
ADMIN_AVATAR = os.getenv(
    "ADMIN_AVATAR", "https://api.dicebear.com/9.x/thumbs/svg?seed=onechan_admin"
)


async def seed_admin() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == ADMIN_USERNAME))
        existing = result.scalar_one_or_none()

        password_hash = bcrypt.hashpw(
            ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        if existing:
            existing.password = password_hash
            existing.bio = ADMIN_BIO
            existing.avatar = ADMIN_AVATAR
            existing.role = Role.ADMIN
            existing.is_active = True
            await session.commit()
            print(f"Updated admin user: {ADMIN_USERNAME}")
            return

        user = User(
            username=ADMIN_USERNAME,
            password=password_hash,
            bio=ADMIN_BIO,
            avatar=ADMIN_AVATAR,
            role=Role.ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user: {ADMIN_USERNAME}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
