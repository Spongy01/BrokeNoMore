from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.thread_repo import ThreadRepository

_repo = ThreadRepository()


class ThreadService:

    async def validate_access(
        self, session: AsyncSession, thread_id: str, user_id: str
    ) -> None:
        owner = await _repo.get_owner(session, thread_id)
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found",
            )
        if owner != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

    async def register(
        self, session: AsyncSession, thread_id: str, user_id: str
    ) -> None:
        owner = await _repo.get_owner(session, thread_id)
        if owner is None:
            await _repo.create(session, thread_id, user_id)
