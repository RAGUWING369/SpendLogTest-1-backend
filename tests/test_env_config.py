"""
Tests for TASK-002: Backend .env.example file.

Verifies that .env.example exists at the repository root, contains every
required environment variable with a safe placeholder value, and that the
.gitignore file properly excludes the real .env file from version control.

These tests are intentionally file-level checks — they guard against a missing
or misconfigured environment template, not against application runtime behaviour
(which is tested from TASK-004 onwards when app/ exists).

Coverage note: this module covers no app/ source lines (app/ does not exist yet).
Coverage over app/ is enforced per-module from TASK-004 onward.
"""

import pathlib
import re

import pytest

# ---------------------------------------------------------------------------
# Named constants — no magic strings in assertions
# ---------------------------------------------------------------------------

_REPO_ROOT = pathlib.Path(__file__).parent.parent

_ENV_EXAMPLE_PATH = _REPO_ROOT / ".env.example"
_GITIGNORE_PATH = _REPO_ROOT / ".gitignore"

# The 6 required environment variable names as specified in the project backlog.
# Variable naming follows the pydantic-settings BaseSettings convention used
# throughout the FastAPI application (TASK-004 onward).
_REQUIRED_ENV_VARS: list[str] = [
    "DATABASE_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "FRONTEND_URL",
]

# The DATABASE_URL must use the asyncpg driver — SQLAlchemy async ORM requires it.
_ASYNCPG_URL_PREFIX = "postgresql+asyncpg://"

# The JWT algorithm must be HS256 — symmetric HMAC-SHA256 as specified in backlog.
_EXPECTED_ALGORITHM = "HS256"

# A real secret key would be at least 32 characters of hex or random bytes.
# These placeholder strings are intentionally short/generic and must NOT look
# like a real high-entropy secret.
_FORBIDDEN_REAL_SECRET_PATTERNS = [
    # Real Supabase, Railway, AWS RDS endpoints
    r"\.supabase\.co",
    r"\.railway\.app",
    r"rds\.amazonaws\.com",
    r"\.neon\.tech",
    # Real JWT secrets are 64-char hex strings; placeholder must not look like one.
    # We check it's NOT a 64+ char hex string.
    # (We assert absence of real infrastructure hostnames, not length directly.)
]

# ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer in a sane range.
_MIN_ACCESS_TOKEN_MINUTES = 1
_MAX_ACCESS_TOKEN_MINUTES = 1440  # 24 hours — beyond this defeats the purpose

# REFRESH_TOKEN_EXPIRE_DAYS must be a positive integer in a sane range.
_MIN_REFRESH_TOKEN_DAYS = 1
_MAX_REFRESH_TOKEN_DAYS = 90  # 90 days is the outer practical limit for a refresh token

# ENVIRONMENT must be one of the allowed values.
_ALLOWED_ENVIRONMENT_VALUES = {"development", "testing", "production"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_env_file(path: pathlib.Path) -> dict[str, str]:
    """Parse a .env-style file into a dict of {VAR_NAME: value}.

    Lines that are empty or start with '#' are skipped.
    Lines of the form KEY=value are parsed; the value may be empty.
    """
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip()
    return result


# ---------------------------------------------------------------------------
# AC-1: .env.example file existence and required variable coverage
# ---------------------------------------------------------------------------


def test_env_example_file_exists() -> None:
    """.env.example must be present at the repository root (acceptance criterion 1)."""
    assert _ENV_EXAMPLE_PATH.exists(), (
        f".env.example not found at {_ENV_EXAMPLE_PATH}. "
        "Create it by copying .env.example from the repository root."
    )
    assert _ENV_EXAMPLE_PATH.is_file(), f"{_ENV_EXAMPLE_PATH} exists but is not a file"


@pytest.mark.parametrize("var_name", _REQUIRED_ENV_VARS)
def test_env_example_contains_required_var(var_name: str) -> None:
    """Each of the 6 required variable names must appear in .env.example."""
    assert (
        _ENV_EXAMPLE_PATH.exists()
    ), ".env.example is missing — run test_env_example_file_exists first"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    assert var_name in env_vars, (
        f"Required variable '{var_name}' is missing from .env.example. "
        f"Found variables: {sorted(env_vars.keys())}"
    )


def test_env_example_has_no_empty_required_values() -> None:
    """Each required variable must have a non-empty placeholder value.

    An empty value means the developer has no guidance on what format to use.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    for var in _REQUIRED_ENV_VARS:
        if var in env_vars:
            assert env_vars[var] != "", (
                f"Required variable '{var}' has an empty placeholder in .env.example. "
                "Provide a descriptive placeholder value."
            )


def test_env_example_database_url_uses_asyncpg_driver() -> None:
    """DATABASE_URL placeholder must use the postgresql+asyncpg:// dialect.

    SQLAlchemy async ORM requires the asyncpg driver; using psycopg2 or the
    plain postgresql:// scheme will cause runtime failures.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    db_url = env_vars.get("DATABASE_URL", "")
    assert db_url.startswith(_ASYNCPG_URL_PREFIX), (
        f"DATABASE_URL must start with '{_ASYNCPG_URL_PREFIX}' to use the asyncpg driver. "
        f"Found: '{db_url}'"
    )


def test_env_example_algorithm_is_hs256() -> None:
    """ALGORITHM must be set to HS256 in the placeholder.

    The auth service (TASK-010) signs and verifies JWTs with HS256.
    Changing this without an ADR would silently break token verification.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    algorithm = env_vars.get("ALGORITHM", "")
    assert algorithm == _EXPECTED_ALGORITHM, (
        f"ALGORITHM must be '{_EXPECTED_ALGORITHM}' in .env.example. "
        f"Found: '{algorithm}'"
    )


def test_env_example_access_token_expire_minutes_is_valid_integer() -> None:
    """ACCESS_TOKEN_EXPIRE_MINUTES placeholder must be a positive integer in range [1, 1440].

    The application reads this with pydantic-settings as an int field; a non-integer
    placeholder will cause a startup ValidationError.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    raw_value = env_vars.get("ACCESS_TOKEN_EXPIRE_MINUTES", "")
    assert (
        raw_value.isdigit()
    ), f"ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer. Found: '{raw_value}'"
    minutes = int(raw_value)
    assert _MIN_ACCESS_TOKEN_MINUTES <= minutes <= _MAX_ACCESS_TOKEN_MINUTES, (
        f"ACCESS_TOKEN_EXPIRE_MINUTES must be between {_MIN_ACCESS_TOKEN_MINUTES} and "
        f"{_MAX_ACCESS_TOKEN_MINUTES}. Found: {minutes}"
    )


def test_env_example_refresh_token_expire_days_is_valid_integer() -> None:
    """REFRESH_TOKEN_EXPIRE_DAYS placeholder must be a positive integer in range [1, 90].

    The application reads this with pydantic-settings as an int field; a non-integer
    placeholder will cause a startup ValidationError.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    raw_value = env_vars.get("REFRESH_TOKEN_EXPIRE_DAYS", "")
    assert (
        raw_value.isdigit()
    ), f"REFRESH_TOKEN_EXPIRE_DAYS must be a positive integer. Found: '{raw_value}'"
    days = int(raw_value)
    assert _MIN_REFRESH_TOKEN_DAYS <= days <= _MAX_REFRESH_TOKEN_DAYS, (
        f"REFRESH_TOKEN_EXPIRE_DAYS must be between {_MIN_REFRESH_TOKEN_DAYS} and "
        f"{_MAX_REFRESH_TOKEN_DAYS}. Found: {days}"
    )


def test_env_example_frontend_url_is_valid_http_url() -> None:
    """FRONTEND_URL placeholder must be a valid HTTP/HTTPS URL.

    FastAPI's CORS middleware receives this value; a non-URL value will
    silently misconfigure CORS and block all frontend requests.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    frontend_url = env_vars.get("FRONTEND_URL", "")
    assert frontend_url.startswith("http://") or frontend_url.startswith(
        "https://"
    ), f"FRONTEND_URL must start with 'http://' or 'https://'. Found: '{frontend_url}'"


# ---------------------------------------------------------------------------
# AC-1 continued: no real secrets in placeholder values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("forbidden_pattern", _FORBIDDEN_REAL_SECRET_PATTERNS)
def test_env_example_contains_no_real_infrastructure_endpoints(
    forbidden_pattern: str,
) -> None:
    """.env.example must not contain real cloud infrastructure hostnames.

    Committing a real DATABASE_URL with a Supabase or Railway hostname
    would expose the database password in version control history.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    content = _ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    match = re.search(forbidden_pattern, content)
    assert match is None, (
        f".env.example contains a real infrastructure endpoint matching "
        f"pattern '{forbidden_pattern}'. Replace with a safe placeholder."
    )


def test_env_example_secret_key_is_placeholder_not_real_secret() -> None:
    """SECRET_KEY placeholder must NOT look like a real high-entropy secret.

    A real PyJWT secret key is a 64-character hex string (from secrets.token_hex(32)).
    The placeholder must be a human-readable instruction string, not an actual key.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    secret_key = env_vars.get("SECRET_KEY", "")
    # A real secret from secrets.token_hex(32) is exactly 64 hex chars.
    # Reject placeholder values that look like real secrets.
    is_real_hex_secret = bool(re.fullmatch(r"[0-9a-f]{64}", secret_key))
    assert not is_real_hex_secret, (
        "SECRET_KEY in .env.example appears to be a real secret (64-char hex string). "
        "Replace it with a human-readable placeholder like "
        "'change-me-generate-a-secure-random-secret-key'."
    )


# ---------------------------------------------------------------------------
# AC-3: .gitignore excludes .env
# ---------------------------------------------------------------------------


def test_gitignore_file_exists() -> None:
    """.gitignore must be present at the repository root (acceptance criterion 3)."""
    assert _GITIGNORE_PATH.exists(), (
        f".gitignore not found at {_GITIGNORE_PATH}. "
        "Create it to prevent .env from being accidentally committed."
    )
    assert _GITIGNORE_PATH.is_file(), f"{_GITIGNORE_PATH} exists but is not a file"


def test_gitignore_excludes_env_file() -> None:
    """.gitignore must contain a pattern that excludes the .env file.

    Without this, a developer running `git add .` will accidentally commit their
    .env file containing DATABASE_URL credentials and SECRET_KEY.
    """
    assert (
        _GITIGNORE_PATH.exists()
    ), ".gitignore is missing — see test_gitignore_file_exists"
    content = _GITIGNORE_PATH.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    # Accept any of: ".env", ".env*", ".env.*", ".env.local", etc.
    env_excluded = any(
        line == ".env" or line.startswith(".env")
        for line in lines
        if not line.startswith("#")
    )
    assert env_excluded, (
        ".gitignore does not exclude .env. "
        "Add '.env' on its own line to prevent accidental secret commits."
    )


def test_gitignore_excludes_venv_directory() -> None:
    """.gitignore must exclude the .venv/ virtual environment directory.

    Virtual environment contents (gigabytes of packages) must never be committed.
    """
    assert _GITIGNORE_PATH.exists(), ".gitignore is missing"
    content = _GITIGNORE_PATH.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    venv_excluded = any(
        line in {".venv/", ".venv", "venv/", "venv"}
        for line in lines
        if not line.startswith("#")
    )
    assert venv_excluded, (
        ".gitignore does not exclude the .venv/ directory. "
        "Add '.venv/' to prevent committing the virtual environment."
    )


def test_no_actual_env_file_at_repo_root() -> None:
    """The real .env file must NOT exist at the repository root.

    If it exists, it either contains real secrets (a security risk) or it
    was accidentally committed. This test guards against both.
    """
    env_file = _REPO_ROOT / ".env"
    assert not env_file.exists(), (
        f"A .env file was found at {env_file}. "
        "This file must not be committed — it may contain real secrets. "
        "Add it to .gitignore and remove it from the working tree."
    )


# ---------------------------------------------------------------------------
# Structural completeness checks
# ---------------------------------------------------------------------------


def test_env_example_is_readable_utf8() -> None:
    """.env.example must be valid UTF-8 text (no binary content).

    Editors and shell tools (source, dotenv) expect UTF-8 or ASCII env files.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    try:
        content = _ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
        assert len(content) > 0, ".env.example is empty"
    except UnicodeDecodeError as exc:
        pytest.fail(f".env.example is not valid UTF-8: {exc}")


def test_env_example_has_at_least_six_variables() -> None:
    """.env.example must define at least the 6 required variables.

    This is a count-based guard separate from the parametrized per-variable
    tests — it catches a file that has the right names but also accidentally
    removes others.
    """
    assert _ENV_EXAMPLE_PATH.exists(), ".env.example is missing"
    env_vars = _parse_env_file(_ENV_EXAMPLE_PATH)
    assert len(env_vars) >= len(_REQUIRED_ENV_VARS), (
        f".env.example defines only {len(env_vars)} variable(s); "
        f"at least {len(_REQUIRED_ENV_VARS)} are required."
    )


def test_requirements_txt_exists() -> None:
    """requirements.txt must be present at the repository root.

    It is referenced by requirements-dev.txt and by the Dockerfile (TASK-008).
    Without it, `pip install -r requirements.txt` fails on a clean clone.
    """
    req_file = _REPO_ROOT / "requirements.txt"
    assert req_file.exists(), "requirements.txt is missing from the repository root"


def test_requirements_dev_txt_exists() -> None:
    """requirements-dev.txt must be present at the repository root.

    The CI pipeline and local development environment both rely on it for
    pytest, black, isort, and httpx.
    """
    req_dev_file = _REPO_ROOT / "requirements-dev.txt"
    assert (
        req_dev_file.exists()
    ), "requirements-dev.txt is missing from the repository root"


def test_requirements_dev_txt_references_requirements() -> None:
    """requirements-dev.txt must extend requirements.txt via '-r requirements.txt'.

    This ensures one install command covers both production and dev dependencies.
    """
    req_dev_file = _REPO_ROOT / "requirements-dev.txt"
    assert req_dev_file.exists(), "requirements-dev.txt is missing"
    content = req_dev_file.read_text(encoding="utf-8")
    assert "-r requirements.txt" in content, (
        "requirements-dev.txt must include '-r requirements.txt' "
        "so that production dependencies are installed in the dev environment."
    )
