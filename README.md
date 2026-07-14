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
.venv\Scripts\activate.bat

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
# Edit .env — fill in DATABASE_URL and SECRET_KEY at minimum
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
OpenAPI docs: `http://localhost:8000/docs`  
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

See `.env.example` for the full list with placeholder values. Copy it to `.env` before starting the server.

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL async connection string (`postgresql+asyncpg://user:pass@host/dbname`) |
| `SECRET_KEY` | 32+ character random string used to sign JWT tokens |
| `ALGORITHM` | JWT signing algorithm — default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime in minutes — default `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime in days — default `7` |
| `FRONTEND_URL` | Frontend origin allowed by CORS (e.g. `http://localhost:5173`) |
