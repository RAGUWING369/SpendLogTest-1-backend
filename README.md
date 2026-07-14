# SpendLog — Backend

FastAPI-based REST API for the SpendLog personal expense tracking application.

## Tech Stack

- **Python 3.12** · FastAPI 0.111.x · Pydantic v2 · SQLAlchemy 2.x (async)
- **Database:** PostgreSQL 16 via asyncpg; Alembic for migrations
- **Auth:** python-jose (HS256 JWT) + bcrypt (cost factor 12)
- **Testing:** pytest + pytest-asyncio + pytest-cov (≥ 90% coverage on auth/expense modules)

## Local Development Setup

### 1. Prerequisites

- Python 3.12+ installed
- PostgreSQL 16 running locally (or a Supabase project URL)

### 2. Create and activate the virtual environment

```bash
# Create
python -m venv .venv

# Activate — macOS/Linux
source .venv/bin/activate

# Activate — Windows (Command Prompt)
.venv\Scripts\activate

# Activate — Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env — fill in DATABASE_URL and JWT_SECRET at minimum
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.
OpenAPI docs: `http://localhost:8000/api/v1/docs`
Health check: `http://localhost:8000/api/v1/health`

## Running Tests

```bash
pytest --cov=app --cov-report=term-missing
```

## Code Quality

```bash
# Format
black app/

# Sort imports
isort app/

# Lint
flake8 app/
```

## Required Environment Variables

See `.env.example` (created in TASK-002) for the full list with placeholder values.

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `JWT_SECRET` | 32+ character random string for JWT signing |
| `JWT_ALGORITHM` | JWT algorithm — default `HS256` |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `http://localhost:5173`) |
| `ENVIRONMENT` | `development` or `production` |
| `SENTRY_DSN` | Optional — Sentry error tracking DSN (leave blank to disable) |
