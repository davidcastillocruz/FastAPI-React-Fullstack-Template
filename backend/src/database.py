from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.settings import settings

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
# The naming convention gives every index and constraint a predictable name (uq_users_email...),
# so Alembic can find them later to change or drop them
class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


# FastAPI dependency: one session per request, closed (and rolled back if needed) when it ends
async def get_db() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


# Database session of the request, in an endpoint: db: DbSession
DbSession = Annotated[AsyncSession, Depends(get_db)]
