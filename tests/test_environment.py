"""
Tests for TASK-001: Python virtual environment setup.

Verifies that every package listed in requirements.txt is importable, proving
that `pip install -r requirements.txt` completed successfully in the active
Python environment. These tests are intentionally lightweight — they guard
against a missing or broken install, not against package behaviour.
"""

import importlib
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Named constants — no magic strings in assertions
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parent.parent

# Top-level module names to import for each requirements.txt entry.
# Using the public import name, not the distribution name (e.g. "jwt" not "PyJWT").
_REQUIRED_PACKAGES: list[tuple[str, str]] = [
    ("fastapi", "FastAPI web framework"),
    ("uvicorn", "ASGI server"),
    ("pydantic", "Data validation (Pydantic v2)"),
    ("pydantic_settings", "Pydantic Settings (BaseSettings)"),
    ("sqlalchemy", "SQLAlchemy async ORM"),
    ("asyncpg", "asyncpg PostgreSQL driver"),
    ("alembic", "Alembic database migrations"),
    ("jwt", "PyJWT authentication library"),
    ("bcrypt", "bcrypt password hashing"),
    ("httpx", "HTTPX async HTTP client"),
    ("pytest", "pytest test runner"),
    ("pytest_asyncio", "pytest-asyncio plugin"),
    ("black", "Black code formatter"),
    ("isort", "isort import sorter"),
]


# ---------------------------------------------------------------------------
# Package availability tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_name,description", _REQUIRED_PACKAGES)
def test_required_package_is_importable(module_name: str, description: str) -> None:
    """Each entry in requirements.txt must be importable after `pip install`."""
    module = importlib.import_module(module_name)
    assert module is not None, f"{description} ({module_name}) could not be imported"


def test_pydantic_is_v2() -> None:
    """Confirm Pydantic v2 is installed — Pydantic v1 is not supported."""
    import pydantic

    major = int(pydantic.VERSION.split(".")[0])
    assert major >= 2, f"Pydantic v2 required; found v{pydantic.VERSION}"


def test_sqlalchemy_is_v2() -> None:
    """Confirm SQLAlchemy 2.x is installed — async ORM requires 2.x."""
    import sqlalchemy

    major = int(sqlalchemy.__version__.split(".")[0])
    assert major >= 2, f"SQLAlchemy 2.x required; found v{sqlalchemy.__version__}"


def test_fastapi_minimum_version() -> None:
    """Confirm FastAPI >= 0.111 is installed per the project tech-stack spec."""
    import fastapi

    parts = fastapi.__version__.split(".")
    major, minor = int(parts[0]), int(parts[1])
    assert (major, minor) >= (
        0,
        111,
    ), f"FastAPI >= 0.111 required; found v{fastapi.__version__}"


def test_pyjwt_not_python_jose() -> None:
    """PyJWT must be present; python-jose must NOT be installed.

    python-jose 3.3.0 is unmaintained and carries a known algorithm-confusion
    vulnerability (CVE-2024-33664).  PyJWT 2.x is the security-correct
    replacement.  This test guards against accidental reintroduction of
    python-jose.
    """
    # PyJWT must be importable
    jwt_module = importlib.import_module("jwt")
    assert jwt_module is not None

    # python-jose must NOT be installed
    with pytest.raises(ImportError):
        importlib.import_module("jose")


# ---------------------------------------------------------------------------
# .gitignore content tests
# ---------------------------------------------------------------------------


def test_gitignore_excludes_venv() -> None:
    """.gitignore must list .venv/ so the virtual environment is never committed."""
    gitignore = _REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore file is missing from the repository root"
    content = gitignore.read_text(encoding="utf-8")
    assert ".venv/" in content, ".gitignore must contain '.venv/' entry"


def test_gitignore_excludes_env_file() -> None:
    """.gitignore must list .env so secrets are never committed."""
    gitignore = _REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore file is missing from the repository root"
    content = gitignore.read_text(encoding="utf-8")
    assert ".env" in content, ".gitignore must contain '.env' entry"


# ---------------------------------------------------------------------------
# .env.example completeness tests
# ---------------------------------------------------------------------------


_REQUIRED_ENV_VARS: list[str] = [
    "DATABASE_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "FRONTEND_URL",
    "ENVIRONMENT",
]


@pytest.mark.parametrize("var_name", _REQUIRED_ENV_VARS)
def test_env_example_contains_variable(var_name: str) -> None:
    """.env.example must document every required environment variable."""
    env_example = _REPO_ROOT / ".env.example"
    assert env_example.exists(), ".env.example is missing from the repository root"
    content = env_example.read_text(encoding="utf-8")
    assert var_name in content, f".env.example is missing required variable: {var_name}"


def test_env_example_contains_no_real_secrets() -> None:
    """.env.example must not contain a production DATABASE_URL or real secret key."""
    env_example = _REPO_ROOT / ".env.example"
    assert env_example.exists()
    content = env_example.read_text(encoding="utf-8")

    # A real Supabase or Railway DATABASE_URL contains a non-placeholder host
    forbidden_patterns = ["supabase.co", "railway.app", "rds.amazonaws.com"]
    for pattern in forbidden_patterns:
        assert (
            pattern not in content
        ), f".env.example must not contain real infrastructure host: {pattern}"


def test_requirements_txt_exists() -> None:
    """requirements.txt must be present at the repository root."""
    req_file = _REPO_ROOT / "requirements.txt"
    assert req_file.exists(), "requirements.txt is missing from the repository root"


def test_requirements_txt_contains_pyjwt_not_python_jose() -> None:
    """requirements.txt must pin PyJWT, not the unmaintained python-jose.

    The check ignores comment lines (lines starting with '#') so that a comment
    explaining *why* PyJWT was chosen over python-jose does not trigger a false
    positive.
    """
    req_file = _REPO_ROOT / "requirements.txt"
    assert req_file.exists()

    raw = req_file.read_text(encoding="utf-8")
    # Filter to dependency lines only (strip comments and blank lines)
    dep_lines = [
        line.split("#")[0].strip().lower()
        for line in raw.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    dep_content = "\n".join(dep_lines)

    assert "pyjwt" in dep_content, "requirements.txt must list PyJWT"
    assert (
        "python-jose" not in dep_content
    ), "requirements.txt must not list python-jose (unmaintained, CVE-2024-33664)"
