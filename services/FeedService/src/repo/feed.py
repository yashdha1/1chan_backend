import uuid
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert 
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.Feed import tags, post_tags, user_tag_profile, post_viewed


class FeedRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_weights(self, user_id) -> dict | None:
        q = select(user_tag_profile.weights).where(user_tag_profile.user_id == user_id)
        row = (await self.db.execute(q)).scalar_one_or_none()
        if not row:
            return None
        return row  # jsonb to dict

    async def upsert_weights(self, user_id, weights_delta: dict):
        """Merge incoming delta into existing JSONB weights."""
        current = await self.get_user_weights(user_id) or {}
        for tid, delta in weights_delta.items():
            current[str(tid)] = current.get(str(tid), 0) + delta

        stmt = (
            insert(user_tag_profile)
            .values(user_id=user_id, weights=current)
            .on_conflict_do_update(
                index_elements=[user_tag_profile.user_id],
                set_={"weights": current, "updated_at": func.now()},
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    def _unseen_subq(self, user_id):
        """seen posts subquery"""
        return select(post_viewed.post_id).where(post_viewed.user_id == user_id)

    async def mark_viewed(self, user_id, post_ids: list[int]):
        if not post_ids:
            return
        rows = [{"user_id": user_id, "post_id": pid} for pid in post_ids]
        stmt = insert(post_viewed).values(rows).on_conflict_do_nothing()
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_preference_pool_for_tag(
        self, tag_id, user_id, limit: int, exclude_post_ids: list[int] | None = None
    ) -> list[int]:
        conditions = [
            post_tags.tag_id == tag_id,
            post_tags.post_id.notin_(self._unseen_subq(user_id)),
        ]
        if exclude_post_ids:
            conditions.append(post_tags.post_id.notin_(exclude_post_ids))
        q = (
            select(post_tags.post_id)
            .where(*conditions)
            .group_by(post_tags.post_id)
            .order_by(post_tags.post_id.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(q)).scalars().all()
        return list(rows)

    async def get_random_pool(
        self, user_id, exclude_ids: list[int], limit: int
    ) -> list[int]:
        conditions = [post_tags.post_id.notin_(self._unseen_subq(user_id))]
        if exclude_ids:
            conditions.append(post_tags.post_id.notin_(exclude_ids))
        distinct_posts = (
            select(post_tags.post_id)
            .where(*conditions)
            .group_by(post_tags.post_id)
            .subquery()
        )
        q = select(distinct_posts.c.post_id).order_by(func.random()).limit(limit)
        rows = (await self.db.execute(q)).scalars().all()
        return list(rows)

    async def get_cold_start_pool(self, user_id, limit: int) -> list[int]:
        distinct_posts = (
            select(post_tags.post_id)
            .where(post_tags.post_id.notin_(self._unseen_subq(user_id)))
            .group_by(post_tags.post_id)
            .subquery()
        )
        q = select(distinct_posts.c.post_id).order_by(func.random()).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_latest_pool(self, user_id, limit: int) -> list[int]:
        q = (
            select(post_tags.post_id)
            .where(post_tags.post_id.notin_(self._unseen_subq(user_id)))
            .group_by(post_tags.post_id)
            .order_by(func.max(post_tags.created_at).desc(), post_tags.post_id.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(q)).scalars().all()
        return list(rows)

    async def get_community_pool(self, user_id, limit: int) -> list[int]:
        q = (
            select(post_tags.post_id)
            .select_from(post_tags.__table__.join(tags, post_tags.tag_id == tags.id))
            .where(post_tags.post_id.notin_(self._unseen_subq(user_id)))
            .group_by(post_tags.post_id)
            .order_by(
                func.max(tags.post_count).desc(),
                func.max(post_tags.created_at).desc(),
                post_tags.post_id.desc(),
            )
            .limit(limit)
        )
        rows = (await self.db.execute(q)).scalars().all()
        return list(rows)

    # crud

    async def add_tag(self, name: str):
        stmt = insert(tags).values(name=name).on_conflict_do_nothing()
        await self.db.execute(stmt)
        await self.db.commit()

    async def add_post_tags(self, post_id: str, tag_names: list[str]):
        print("Running the query")
        tag_rows = ( 
            await self.db.execute(select(tags).where(tags.name.in_(tag_names)))
        ).scalars().all()
        print(f"Found tags: {tag_rows}")
        if not tag_rows:
            return
        pid = uuid.UUID(post_id) if isinstance(post_id, str) else post_id
        rows = [{"post_id": pid, "tag_id": t.id} for t in tag_rows]

        stmt = insert(post_tags).values(rows).on_conflict_do_nothing()
        await self.db.execute(stmt)
        print("Post-tags inserted/updated")
        await self.db.commit()

    async def get_all_tags(self):
        rows = (await self.db.execute(select(tags))).scalars().all()
        return rows
