from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./brokenomore.db"

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
