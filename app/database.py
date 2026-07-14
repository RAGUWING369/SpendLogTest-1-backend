"""
Async database engine and session factory (SQLAlchemy 2.x + asyncpg).

The engine is created once at module import time.  Instantiating the engine
does NOT open a database connection — connections are established on first
use via the async connection pool.

Pool sizing rationale (architecture document — capacity planning):
  pool_size=5     : minimum sustained connections
  max_overflow=15 : burst headroom (total max = 20, matching Supabase free-tier
                    Supavisor transaction-mode connection limit)
  pool_pre_ping=True : validates each connection before use, guarding against
                       stale connections caused by PgBouncer idle timeouts.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Async engine — asyncpg driver.
# echo=False keeps SQL out of structured logs in all environments.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=15,
    pool_pre_ping=True,
    echo=False,
)

# Session factory — expire_on_commit=False prevents implicit lazy-load errors
# when Pydantic serialises ORM objects after a commit.
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides one database session per request.

    The session is automatically closed on exit.  Any uncommitted transaction
    is rolled back if an exception propagates out of the route handler.

    Usage::

        @router.get("/example")
        async def example(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionFactory() as session:
        yield session
