"""FastAPI application factory.

Configures:
- Structured JSON logging (must happen before any logger.xxx calls)
- CORS middleware (allow-list: FRONTEND_URL only)
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

# CORS: only the configured frontend origin is allowed.
# All other origins are silently rejected by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")

_logger.info("SpendLog API initialised")
