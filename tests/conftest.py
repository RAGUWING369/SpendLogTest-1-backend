"""
Shared pytest fixtures for the SpendLog backend test suite.

Environment variables are set at the TOP of this file (before any app imports)
so that pydantic-settings can read them when ``Settings()`` is first instantiated.
``os.environ.setdefault`` is used so real CI / developer values are never
overridden — the defaults here are safe, non-secret placeholders.

Async test mode is configured globally in setup.cfg::

    [tool:pytest]
    asyncio_mode = auto

Every ``async def test_*`` function is automatically treated as an asyncio
test without needing the ``@pytest.mark.asyncio`` decorator.

Fixtures:
    async_client  — AsyncClient pointed at the ASGI app (no real server needed)

Future fixtures (added by later tasks):
    db_session    — TASK-012: async SQLAlchemy session backed by a test DB
    auth_headers  — TASK-012: pre-authenticated Bearer token header
    test_user_a / test_user_b — TASK-019: two isolated test users
"""

import os

# ---------------------------------------------------------------------------
# Required environment variables — set BEFORE any app.* imports so that
# pydantic-settings resolves them when Settings() is instantiated.
# ---------------------------------------------------------------------------
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/spendlog_test",
)
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-unit-tests-minimum-32-characters-long",
)
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

# ---------------------------------------------------------------------------
# Standard library / third-party imports (after env vars are set)
# ---------------------------------------------------------------------------
import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# HTTP test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
async def async_client() -> AsyncClient:
    """
    Async HTTP test client for the FastAPI application.

    Uses ``ASGITransport`` to call the ASGI app directly — no real TCP
    server is started.  This means no network round-trips and no port
    conflicts in CI.

    The client is scoped to the test function: a fresh client is created for
    each test, which keeps tests independent of each other's session state.

    Endpoints that do NOT touch the database (e.g. ``GET /api/v1/health``)
    work without a live PostgreSQL instance; the engine is created lazily and
    only connects when a session is actually opened.
    """
    from app.main import app  # imported here to honour env-var setup above

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
