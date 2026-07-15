"""Async SQLAlchemy database engine, session factory, and ORM base class.

The engine and session factory are created once at module import time and
shared across the application lifetime.  Per-request sessions are obtained
via the ``get_async_session`` FastAPI dependency.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)

# Connection pool tuning — sized for Supabase free tier (max 20 pooled conns).
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 15

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy ORM models."""


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session per request.

    Rolls back the session on any unhandled exception so stale transactions
    never reach the connection pool.

    Yields:
        AsyncSession: A scoped async database session.

    Raises:
        Exception: Re-raises any exception after rolling back the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
