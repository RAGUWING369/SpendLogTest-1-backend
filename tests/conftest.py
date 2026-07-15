"""Shared test configuration and fixtures.

IMPORTANT: Environment variables are set at module level (not inside
fixtures) so they are present BEFORE pytest imports any test file that
transitively imports app modules.  app/config.py calls Settings() at
import time — the variables must already be in os.environ at that point.
"""

import os

# Set all required environment variables before any app module is imported.
# setdefault() preserves any values already injected by the CI environment.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/testdb",
)
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-testing-purposes-only-must-be-32-chars",
)
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("ENVIRONMENT", "test")
