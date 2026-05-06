from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserThread


class ThreadRepository:

    async def get_owner(self, session: AsyncSession, thread_id: str) -> str | None:
        result = await session.execute(
            select(UserThread).where(UserThread.thread_id == thread_id)
        )
        row = result.scalar_one_or_none()
        return row.user_id if row else None

    async def create(self, session: AsyncSession, thread_id: str, user_id: str) -> None:
        session.add(UserThread(thread_id=thread_id, user_id=user_id))
        await session.commit()
