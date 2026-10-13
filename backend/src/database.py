from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core import settings

# Async engine using asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # check connections before using them
)

# Session factory, expire_on_commit=False keeps the objects readable after a commit
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Base class of the models: class User(Base) registers its table
class Base(DeclarativeBase):
    pass


# FastAPI dependency: one session per request, closed (and rolled back if needed) when it ends
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
