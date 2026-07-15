"""Application configuration loaded from environment variables or .env file.

Settings uses Pydantic v2 BaseSettings — values are read from environment
variables first, then from the .env file if present.  All six required
variables must be present; the application will raise a ValidationError at
startup if any are missing.
"""

import logging

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# JWT defaults — kept as named constants to avoid magic numbers in callers.
DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7


class Settings(BaseSettings):
    """Application settings validated and loaded by Pydantic.

    Attributes:
        DATABASE_URL: Async-compatible PostgreSQL URL (postgresql+asyncpg://...).
        SECRET_KEY: HMAC-SHA256 signing secret for JWT tokens.
        ALGORITHM: JWT signing algorithm (default: HS256).
        ACCESS_TOKEN_EXPIRE_MINUTES: Access token TTL in minutes (default: 30).
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh token TTL in days (default: 7).
        FRONTEND_URL: Allowed CORS origin for the SPA frontend.
        ENVIRONMENT: Runtime environment label (development | test | production).
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = DEFAULT_ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS: int = DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS
    FRONTEND_URL: str
    ENVIRONMENT: str = "development"


# Singleton — imported by other modules as ``from app.config import settings``.
settings = Settings()
