"""
Shared pytest fixtures for the SpendLog backend test suite.

Fixtures defined here are available to all test modules under tests/.
This file is intentionally minimal at the TASK-001 stage — database,
HTTP client, and user fixtures will be added in TASK-012 once the
FastAPI application (TASK-004) and schema (TASK-005) are in place.

Async test mode is configured globally in setup.cfg:
    [tool:pytest]
    asyncio_mode = auto

This means every `async def test_*` function is automatically treated
as an asyncio test without needing the @pytest.mark.asyncio decorator.
"""

import pytest


# ---------------------------------------------------------------------------
# Placeholder: no fixtures needed until TASK-004 (app scaffold) is complete.
# The conftest is kept in the repository so that:
#   1. `pytest` can discover the tests/ package and exit 0 on an empty run.
#   2. Future fixture additions have a documented home with clear comments.
# ---------------------------------------------------------------------------
