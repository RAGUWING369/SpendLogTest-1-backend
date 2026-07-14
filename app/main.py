"""
SpendLog FastAPI application entry point.

Responsibility of this module (in order of execution):
1. Configure structured JSON logging (before any logger calls)
2. Create the FastAPI application instance
3. Register CORS middleware (restricts cross-origin access to the configured
   frontend origin — never wildcard)
4. Register per-request HTTP logging middleware
5. Mount API routers under /api/v1

All application secrets and configuration are loaded via app.config.settings;
no hardcoded values are present in this module.
"""

import json
import logging
import sys
import time
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.routers import health

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """
    Serialize each log record to a single-line JSON string.

    Fields included in every record:
    - timestamp  : ISO-8601 local time (without timezone offset for brevity)
    - level      : CRITICAL / ERROR / WARNING / INFO / DEBUG
    - logger     : dotted logger name (e.g. "app.main", "uvicorn.access")
    - message    : the formatted log message
    - module     : Python module name
    - function   : calling function name

    If the record carries an exception, a formatted traceback is appended
    under the "exception" key.  No PII is written by this formatter — callers
    are responsible for not passing PII to the logger.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Return the log record serialised to a JSON string."""
        log_entry: dict = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def _configure_logging() -> None:
    """
    Replace any existing root-logger handlers with a single JSONFormatter handler.

    Called once at module import time so the formatter is in place before
    FastAPI or Uvicorn emit their first log lines.
    """
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = []
    root.addHandler(json_handler)


_configure_logging()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


app = FastAPI(
    title="SpendLog API",
    description="Personal expense tracking REST API",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
# Security architecture constraints:
#   - allow_credentials=False  : tokens live in localStorage, not cookies
#   - No wildcard origins       : only the configured FRONTEND_URL is allowed
#   - localhost:5173 is always included for local Vite dev server access
# ---------------------------------------------------------------------------

_LOCALHOST_DEV_ORIGIN = "http://localhost:5173"

# Always include both the configured frontend URL and the localhost Vite dev
# server — duplicates are deduplicated by the set conversion so the middleware
# receives a clean list regardless of what FRONTEND_URL is set to.
_allowed_origins: list[str] = list({settings.FRONTEND_URL, _LOCALHOST_DEV_ORIGIN})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Per-request logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """
    Emit a structured INFO log for every HTTP request.

    Logged fields: method, path, response status code, and wall-clock
    duration in milliseconds.  Authorization headers and request bodies
    are intentionally excluded — no PII is written to logs.
    """
    start: float = time.monotonic()
    response: Response = await call_next(request)
    duration_ms: float = round((time.monotonic() - start) * 1000, 2)
    logger.info(
        "%s %s %d %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(health.router, prefix="/api/v1")
