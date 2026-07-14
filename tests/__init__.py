# Tests package for SpendLog backend.
#
# Structure (populated by subsequent tasks):
#   tests/
#   ├── conftest.py          — shared fixtures (DB session, HTTP client, users)
#   ├── test_auth.py         — TASK-012: 12-case auth suite (≥ 90% coverage)
#   ├── test_expenses.py     — TASK-019: 13-case expense suite (≥ 90% coverage)
#   └── test_dashboard.py   — TASK-026: 8-case dashboard suite (≥ 90% coverage)
