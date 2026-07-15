"""FastAPI application factory.

Configures:
- Structured JSON logging (must happen before any logger.xxx calls)
- CORS middleware (explicit origin, method, and header allow-lists per security arch)
- OpenAPI docs (disabled in production per ARCH-INF-011)
- All API routers under /api/v1
"""

import json
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health

_LOG_LEVEL = logging.INFO


class _JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production-ready log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise a log record to a single-line JSON string.

        Args:
            record: The log record emitted by a logger.

        Returns:
            str: A JSON-encoded log line with level, name, and message keys.
        """
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def _configure_logging() -> None:
    """Replace the root logger handler with a JSON-formatted stream handler."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    logging.basicConfig(level=_LOG_LEVEL, handlers=[handler], force=True)


_configure_logging()
_logger = logging.getLogger(__name__)

# OpenAPI UI is disabled in production to reduce attack surface (ARCH-INF-011).
_docs_url = None if settings.ENVIRONMENT == "production" else "/docs"
_redoc_url = None if settings.ENVIRONMENT == "production" else "/redoc"

app = FastAPI(
    title="SpendLog API",
    description="Personal expense tracking REST API",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# CORS: exact allow-list per security architecture (section: Network Security Controls).
# Explicit methods and headers enforce least-privilege; credentials mode is disabled
# because the SPA authenticates via Authorization headers, not cookies.
# The Vite dev origin is listed explicitly so local developers can reach a staging
# backend even when FRONTEND_URL points to the production URL.
_CORS_ALLOWED_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST"]
_CORS_ALLOWED_HEADERS = ["Authorization", "Content-Type"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=_CORS_ALLOWED_METHODS,
    allow_headers=_CORS_ALLOWED_HEADERS,
)

app.include_router(health.router, prefix="/api/v1")

_logger.info("SpendLog API initialised")
