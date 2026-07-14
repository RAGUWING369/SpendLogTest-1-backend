"""
Environment sanity tests — TASK-001: Python virtual environment setup.

These tests verify that the development environment is correctly configured:
  1. Python version meets the minimum requirement (3.12+)
  2. All packages from requirements.txt are importable (confirms pip install ran cleanly)
  3. No package version conflicts exist (bcrypt 4.x, pydantic v2)
  4. .gitignore correctly excludes .venv/ and .env while allowing .env.example
  5. .env.example exists at the repo root (so `cp .env.example .env` works on fresh clone)

Run with:
    pytest tests/test_environment.py -v

These tests are intentionally import-only — no application logic is exercised here.
They serve as the automated proof of TASK-001's acceptance criteria.
"""

import importlib
import pathlib
import sys

# ---------------------------------------------------------------------------
# Helper: repo root path (two levels up from this file: tests/ -> repo root)
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).parents[1]


# ── 1. Python version ────────────────────────────────────────────────────────


def test_python_version_is_312_or_higher():
    """
    Python 3.12+ is required per the project tech stack specification.

    TASK-001 AC: `.venv/` activates on macOS/Linux/Windows with Python 3.12.
    """
    major, minor = sys.version_info.major, sys.version_info.minor
    assert (major, minor) >= (3, 12), (
        f"Python 3.12+ required. Found: {major}.{minor}. "
        "Activate the correct virtual environment or upgrade Python."
    )


# ── 2. Core framework package imports ────────────────────────────────────────


def test_fastapi_importable():
    """fastapi 0.111.x must be importable — confirms pip install included the package."""
    fastapi = importlib.import_module("fastapi")
    assert fastapi is not None, "fastapi import returned None"


def test_uvicorn_importable():
    """uvicorn[standard] must be importable as the ASGI server."""
    uvicorn = importlib.import_module("uvicorn")
    assert uvicorn is not None, "uvicorn import returned None"


def test_sqlalchemy_importable():
    """sqlalchemy[asyncio] must be importable with async extension present."""
    sa = importlib.import_module("sqlalchemy")
    assert sa is not None, "sqlalchemy import returned None"
    # Verify async extension is present — requires sqlalchemy[asyncio] extra
    ext_async = importlib.import_module("sqlalchemy.ext.asyncio")
    assert ext_async is not None, "sqlalchemy.ext.asyncio not available"


def test_asyncpg_importable():
    """asyncpg must be importable as the PostgreSQL async driver for SQLAlchemy."""
    asyncpg = importlib.import_module("asyncpg")
    assert asyncpg is not None, "asyncpg import returned None"


def test_alembic_importable():
    """alembic must be importable for database schema migrations."""
    alembic = importlib.import_module("alembic")
    assert alembic is not None, "alembic import returned None"


def test_pydantic_v2_importable():
    """pydantic[email] v2 must be importable — v1 is not compatible."""
    pydantic = importlib.import_module("pydantic")
    assert pydantic is not None, "pydantic import returned None"
    major = int(pydantic.VERSION.split(".")[0])
    assert major == 2, (
        f"Pydantic v2 required. Found v{pydantic.VERSION}. "
        "Check requirements.txt — passlib 1.7.4 pulls in pydantic v1."
    )


def test_pydantic_settings_importable():
    """pydantic-settings must be importable for environment variable loading."""
    pydantic_settings = importlib.import_module("pydantic_settings")
    assert pydantic_settings is not None, "pydantic_settings import returned None"


def test_pydantic_email_validator_importable():
    """email-validator must be importable (installed via pydantic[email] extra)."""
    email_validator = importlib.import_module("email_validator")
    assert email_validator is not None, "email_validator import returned None"


# ── 3. Authentication package imports ────────────────────────────────────────


def test_jose_importable():
    """python-jose[cryptography] must be importable for HS256 JWT operations."""
    jose = importlib.import_module("jose")
    assert jose is not None, "jose import returned None"
    # Confirm cryptography-backed JWT module is available
    jose_jwt = importlib.import_module("jose.jwt")
    assert jose_jwt is not None, "jose.jwt module not available"


def test_bcrypt_importable():
    """
    bcrypt 4.x must be importable for password hashing.

    NOTE: passlib 1.7.4 is intentionally excluded from requirements.txt — it
    is incompatible with bcrypt 4.x at runtime (AttributeError on __about__).
    bcrypt is used directly instead, per TASK-001 requirements.
    """
    bcrypt = importlib.import_module("bcrypt")
    assert bcrypt is not None, "bcrypt import returned None"
    major = int(bcrypt.__version__.split(".")[0])
    assert major >= 4, (
        f"bcrypt 4.x required (used directly, not via passlib). "
        f"Found: {bcrypt.__version__}."
    )


# ── 4. HTTP client + testing tools ───────────────────────────────────────────


def test_httpx_importable():
    """httpx must be importable — used as async HTTP client in integration tests."""
    httpx = importlib.import_module("httpx")
    assert httpx is not None, "httpx import returned None"


def test_pytest_asyncio_importable():
    """pytest-asyncio must be importable to support async test functions."""
    pytest_asyncio = importlib.import_module("pytest_asyncio")
    assert pytest_asyncio is not None, "pytest_asyncio import returned None"


# ── 5. .gitignore correctness ────────────────────────────────────────────────


def test_gitignore_excludes_venv_directory():
    """
    .venv/ must appear in .gitignore.

    TASK-001 AC: virtual environment directory must not be committed.
    """
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore not found at repo root"
    content = gitignore.read_text(encoding="utf-8")
    assert ".venv/" in content, ".venv/ must be listed in .gitignore"


def test_gitignore_excludes_env_file():
    """.env must be excluded from version control — no real secrets committed."""
    gitignore = REPO_ROOT / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    # Either .env or .env.* pattern must be present
    assert ".env" in content, ".env must be excluded in .gitignore"


def test_gitignore_allows_env_example():
    """.env.example must be explicitly permitted via !.env.example negation rule."""
    gitignore = REPO_ROOT / ".gitignore"
    content = gitignore.read_text(encoding="utf-8")
    assert "!.env.example" in content, (
        ".env.example must be allowed via '!.env.example' in .gitignore "
        "so the developer guide file is tracked by git."
    )


# ── 6. .env.example presence and completeness ────────────────────────────────


def test_env_example_exists_at_repo_root():
    """
    .env.example must exist so `cp .env.example .env` succeeds on fresh clone.

    TASK-001 AC: developer setup must be possible from a clean clone.
    Without this file, README step 4 fails immediately.
    """
    env_example = REPO_ROOT / ".env.example"
    assert env_example.exists(), (
        ".env.example not found at repo root. "
        "Developers cannot complete local setup without this template file."
    )


def test_env_example_contains_all_required_variables():
    """
    .env.example must define all 6 required backend environment variables.

    Variables: DATABASE_URL, SECRET_KEY, ALGORITHM,
               ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, FRONTEND_URL.
    These match the TASK-002 specification exactly.
    """
    env_example = REPO_ROOT / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    required_variables = [
        "DATABASE_URL",
        "SECRET_KEY",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "FRONTEND_URL",
    ]
    missing = [var for var in required_variables if var not in content]
    assert not missing, (
        f"The following required variables are missing from .env.example: {missing}"
    )


def test_env_example_uses_placeholder_values_not_real_secrets():
    """
    .env.example must not contain real credentials — only safe placeholder values.

    Checks that SECRET_KEY placeholder does not look like a real secret (hex string).
    """
    env_example = REPO_ROOT / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    # The placeholder for SECRET_KEY must not be a 64-char hex string (real secret)
    for line in content.splitlines():
        if line.startswith("SECRET_KEY="):
            value = line.split("=", 1)[1].strip()
            # A real hex secret would be exactly 64 lowercase hex chars
            is_real_hex_secret = (
                len(value) == 64
                and all(c in "0123456789abcdef" for c in value)
            )
            assert not is_real_hex_secret, (
                "SECRET_KEY in .env.example appears to be a real secret. "
                "Use a placeholder value like 'replace-this-with-a-secure-random-key'."
            )
            break
