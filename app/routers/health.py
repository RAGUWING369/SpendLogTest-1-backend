"""
Health check router — GET /api/v1/health.

Returns a simple liveness response so Railway, Vercel health-check probes,
and the CI smoke test can confirm the server is running without requiring
any database connectivity.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    """
    Liveness check endpoint.

    Returns HTTP 200 with ``{"status": "ok"}`` when the API process is running.
    Does not check database connectivity — use a dedicated readiness endpoint
    for that if needed in future.
    """
    return {"status": "ok"}
