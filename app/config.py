"""
Application configuration — loaded from environment variables and .env file.

Uses pydantic-settings BaseSettings so every required variable is validated
at startup. Missing or wrongly-typed variables raise a ValidationError with
a clear message before the server accepts any traffic.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration for the SpendLog backend.

    Load order (highest priority first):
    1. Process environment variables (set by Railway / CI / developer shell)
    2. .env file (local development; never committed to version control)
    3. Default values defined on each field
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    # asyncpg connection string: postgresql+asyncpg://user:pass@host:port/dbname
    DATABASE_URL: str

    # ── JWT security ─────────────────────────────────────────────────────────
    # Must be ≥ 32 cryptographically random bytes (generate with secrets.token_hex(32))
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Frontend origin allowed by the CORS middleware (no trailing slash)
    FRONTEND_URL: str = "http://localhost:5173"


# Module-level singleton — imported directly by other app modules.
# Populated once at process startup; env-var changes at runtime are not picked up.
settings = Settings()
