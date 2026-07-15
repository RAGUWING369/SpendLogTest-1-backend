"""Tests for the health check endpoint.

Covers:
- GET /api/v1/health happy path (HTTP 200 + correct body)
- CORS: allowed origin receives Access-Control-Allow-Origin header
- CORS: unlisted origin is not reflected back
"""

from httpx import ASGITransport, AsyncClient


async def test_health_returns_200() -> None:
    """GET /api/v1/health must return HTTP 200 OK."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200


async def test_health_returns_correct_body() -> None:
    """GET /api/v1/health must return the JSON body {"status": "ok"}."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.json() == {"status": "ok"}


async def test_health_content_type_is_json() -> None:
    """GET /api/v1/health must return Content-Type: application/json."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert "application/json" in response.headers["content-type"]


async def test_cors_allows_configured_frontend_url() -> None:
    """CORS must reflect the configured FRONTEND_URL in the response header."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"origin": "http://localhost:5173"},
        )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    )


async def test_cors_does_not_reflect_unlisted_origin() -> None:
    """CORS must not add allow-origin header for origins not in the allow-list."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/health",
            headers={"origin": "http://malicious-site.example.com"},
        )

    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        != "http://malicious-site.example.com"
    )


async def test_health_endpoint_exists_at_correct_path() -> None:
    """Health check must live at /api/v1/health — not /health or /api/health."""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        wrong_path_response = await client.get("/health")
        correct_path_response = await client.get("/api/v1/health")

    assert wrong_path_response.status_code == 404
    assert correct_path_response.status_code == 200
