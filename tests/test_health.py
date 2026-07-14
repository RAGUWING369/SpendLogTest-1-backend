"""
Tests for the FastAPI application scaffold (TASK-004).

Coverage targets:
  - app/main.py        : FastAPI app, CORS middleware, logging middleware
  - app/config.py      : Settings loaded from environment variables
  - app/database.py    : Async engine created without live DB connection
  - app/routers/health : GET /api/v1/health endpoint

Acceptance criteria verified:
  [x] GET /api/v1/health → 200 {"status": "ok"}
  [x] CORS allows FRONTEND_URL, blocks unlisted origins
  [x] Pydantic Settings loads from environment
  [x] Structured JSON logging is configured
  [x] pytest discovers test dir and exits 0
"""

import logging

import pytest
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Health endpoint — happy path
# ---------------------------------------------------------------------------


async def test_health_returns_200(async_client: AsyncClient) -> None:
    """GET /api/v1/health must return HTTP 200."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200


async def test_health_returns_correct_body(async_client: AsyncClient) -> None:
    """GET /api/v1/health must return exactly {"status": "ok"}."""
    response = await async_client.get("/api/v1/health")
    assert response.json() == {"status": "ok"}


async def test_health_content_type_is_json(async_client: AsyncClient) -> None:
    """GET /api/v1/health must return application/json content type."""
    response = await async_client.get("/api/v1/health")
    assert "application/json" in response.headers["content-type"]


async def test_health_method_not_allowed_for_post(async_client: AsyncClient) -> None:
    """POST /api/v1/health must return 405 Method Not Allowed."""
    response = await async_client.post("/api/v1/health")
    assert response.status_code == 405


# ---------------------------------------------------------------------------
# Health endpoint — non-existent path
# ---------------------------------------------------------------------------


async def test_unknown_path_returns_404(async_client: AsyncClient) -> None:
    """Requests to undefined paths must return HTTP 404."""
    response = await async_client.get("/api/v1/does-not-exist")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------


async def test_cors_allows_configured_frontend_url() -> None:
    """
    CORS middleware must reflect Access-Control-Allow-Origin for the configured
    FRONTEND_URL.  The header value must exactly match the request Origin.
    """
    from app.config import settings
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": settings.FRONTEND_URL},
        )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == settings.FRONTEND_URL


async def test_cors_allows_localhost_dev_origin() -> None:
    """
    The Vite dev server origin (http://localhost:5173) must always be allowed,
    even when FRONTEND_URL points to a production domain.
    """
    from app.main import app

    localhost_origin = "http://localhost:5173"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": localhost_origin},
        )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == localhost_origin


async def test_cors_does_not_reflect_unlisted_origin() -> None:
    """
    CORS middleware must NOT set Access-Control-Allow-Origin for an origin that
    is not in the allowed list.  The browser will block the response.
    """
    from app.main import app

    disallowed_origin = "https://malicious-site.example.com"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": disallowed_origin},
        )

    # The response itself arrives (server-side; browser blocks it client-side),
    # but the CORS header must NOT be set for the disallowed origin.
    assert response.headers.get("access-control-allow-origin") is None


async def test_cors_preflight_returns_200_for_allowed_origin() -> None:
    """
    OPTIONS preflight for an allowed origin must return 200 with the
    Access-Control-Allow-Origin header.
    """
    from app.config import settings
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": settings.FRONTEND_URL,
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == settings.FRONTEND_URL
    )


async def test_cors_credentials_not_allowed() -> None:
    """
    CORS allow_credentials must be False — tokens are stored in localStorage,
    not sent via cookies.  The Allow-Credentials header must not be 'true'.
    """
    from app.config import settings
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"Origin": settings.FRONTEND_URL},
        )

    allow_credentials = response.headers.get("access-control-allow-credentials", "")
    assert allow_credentials.lower() != "true"


# ---------------------------------------------------------------------------
# Application configuration
# ---------------------------------------------------------------------------


def test_settings_loads_without_error() -> None:
    """
    Settings must load successfully when required env vars are present.
    A ValidationError here means a required variable is missing or mis-typed.
    """
    from app.config import settings

    assert settings is not None


def test_settings_database_url_is_set() -> None:
    """DATABASE_URL must be a non-empty string."""
    from app.config import settings

    assert isinstance(settings.DATABASE_URL, str)
    assert len(settings.DATABASE_URL) > 0


def test_settings_secret_key_is_set() -> None:
    """SECRET_KEY must be a non-empty string (minimum 32 chars enforced at deploy time)."""
    from app.config import settings

    assert isinstance(settings.SECRET_KEY, str)
    assert len(settings.SECRET_KEY) > 0


def test_settings_algorithm_defaults_to_hs256() -> None:
    """ALGORITHM must default to HS256 per the security architecture (ADR-004)."""
    from app.config import settings

    assert settings.ALGORITHM == "HS256"


def test_settings_access_token_expire_is_positive_int() -> None:
    """ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer."""
    from app.config import settings

    assert isinstance(settings.ACCESS_TOKEN_EXPIRE_MINUTES, int)
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0


def test_settings_refresh_token_expire_is_positive_int() -> None:
    """REFRESH_TOKEN_EXPIRE_DAYS must be a positive integer."""
    from app.config import settings

    assert isinstance(settings.REFRESH_TOKEN_EXPIRE_DAYS, int)
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0


def test_settings_frontend_url_is_set() -> None:
    """FRONTEND_URL must be a non-empty string."""
    from app.config import settings

    assert isinstance(settings.FRONTEND_URL, str)
    assert len(settings.FRONTEND_URL) > 0


# ---------------------------------------------------------------------------
# Application structure
# ---------------------------------------------------------------------------


def test_fastapi_app_is_fastapi_instance() -> None:
    """app.main.app must be a FastAPI instance."""
    from fastapi import FastAPI

    from app.main import app

    assert isinstance(app, FastAPI)


def test_fastapi_app_title() -> None:
    """FastAPI app title must be 'SpendLog API'."""
    from app.main import app

    assert app.title == "SpendLog API"


def test_fastapi_app_version() -> None:
    """FastAPI app version must be set to the project version."""
    from app.main import app

    assert app.version == "1.0.0"


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------


def test_json_formatter_is_on_root_logger() -> None:
    """
    Root logger must have at least one handler using JSONFormatter.
    This ensures structured output for all log records across the application.
    """
    from app.main import JSONFormatter  # noqa: PLC0415

    root = logging.getLogger()
    assert root.handlers, "Root logger must have at least one handler"
    assert any(
        isinstance(h.formatter, JSONFormatter) for h in root.handlers
    ), "At least one root-logger handler must use JSONFormatter"


def test_json_formatter_produces_valid_json() -> None:
    """
    JSONFormatter.format() must return a string that parses as valid JSON
    containing the required fields.
    """
    import json

    from app.main import JSONFormatter

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)  # must not raise

    assert data["level"] == "INFO"
    assert data["message"] == "hello world"
    assert data["logger"] == "test.logger"
    assert "timestamp" in data
    assert "module" in data
    assert "function" in data


def test_json_formatter_includes_exception_when_present() -> None:
    """
    JSONFormatter must include the 'exception' key when the log record
    carries exception info.
    """
    import json
    import sys

    from app.main import JSONFormatter

    formatter = JSONFormatter()
    try:
        raise ValueError("test error")
    except ValueError:
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="error occurred",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    data = json.loads(output)

    assert "exception" in data
    assert "ValueError" in data["exception"]


# ---------------------------------------------------------------------------
# Database engine (no live connection needed)
# ---------------------------------------------------------------------------


def test_database_engine_is_async_engine() -> None:
    """
    app.database.engine must be an AsyncEngine.  Creating the engine must
    NOT require a live database connection — connections are deferred until
    a session is opened.
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    from app.database import engine

    assert isinstance(engine, AsyncEngine)


def test_database_session_factory_is_async_session_maker() -> None:
    """AsyncSessionFactory must be an async_sessionmaker instance."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.database import AsyncSessionFactory

    assert isinstance(AsyncSessionFactory, async_sessionmaker)


def test_get_async_session_is_async_generator() -> None:
    """
    get_async_session must be an async generator function (FastAPI dependency
    pattern).  Confirmed by inspecting the function's type at import time.
    """
    import inspect

    from app.database import get_async_session

    assert inspect.isasyncgenfunction(get_async_session)
