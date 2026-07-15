"""Health check router.

Exposes GET /api/v1/health for load-balancer liveness probes and
monitoring uptime checks.  The endpoint is intentionally lightweight —
it does not touch the database or any external service so it returns
fast even when dependencies are degraded.
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return application liveness status.

    Returns:
        dict: ``{"status": "ok"}`` when the application process is running.
    """
    logger.debug("Health check requested")
    return {"status": "ok"}
