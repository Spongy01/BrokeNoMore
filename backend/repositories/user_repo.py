from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PasswordResetToken, User


class UserRepository:

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, session: AsyncSession, user_id: str) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update_password(
        self, session: AsyncSession, user_id: str, hashed_password: str
    ) -> None:
        user = await self.get_by_id(session, user_id)
        if user:
            user.hashed_password = hashed_password
            await session.commit()

    async def save_reset_token(
        self,
        session: AsyncSession,
        token: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        session.add(PasswordResetToken(token=token, user_id=user_id, expires_at=expires_at))
        await session.commit()

    async def get_valid_reset_token(
        self, session: AsyncSession, token: str
    ) -> PasswordResetToken | None:
        now = datetime.utcnow()
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == token,
                PasswordResetToken.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def delete_reset_token(self, session: AsyncSession, token: str) -> None:
        await session.execute(
            delete(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        await session.commit()
