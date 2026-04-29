# Backend

FastAPI backend for the Xiaobaicai Space blog project.

This service exposes public blog APIs and admin APIs, uses MySQL through SQLAlchemy async sessions, and keeps read/write concerns separated with query services, command services, DTO/read models, assemblers, and presenters.

## Stack

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x async
- MySQL with `aiomysql`
- Alembic migrations
- Pydantic Settings
- PyJWT authentication
- Pytest

## Project Layout

- `app/api`: route layer and API composition
- `app/services/queries`: read-side query services
- `app/services/commands`: write-side command services
- `app/core`: settings, database, security, observability, exception handling
- `app/models`: SQLAlchemy ORM models
- `app/schemas`: request/response schemas
- `migrations`: Alembic environment and migration history
- `tests`: unit, route, and opt-in integration smoke tests

## Quick Start

1. Create a `.env` file in the backend root from `.env.example`.
2. Install dependencies.
3. Apply database migrations.
4. Start the development server.

```powershell
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

After startup:

- OpenAPI docs: `http://127.0.0.1:8000/docs`
- readiness check: `http://127.0.0.1:8000/health/ready`
- liveness check: `http://127.0.0.1:8000/health/live`

## Environment Configuration

The backend reads configuration from environment variables via Pydantic Settings.

Core variables from `.env.example`:

- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`: MySQL connection parts
- `DB_ECHO`: SQLAlchemy SQL logging switch, default `false`
- `JWT_SECRET_KEY`: required deployment secret, minimum 32 characters
- `JWT_ALGORITHM`: JWT signing algorithm
- `ACCESS_TOKEN_EXPIRE_MINUTES`: access token lifetime in minutes
- `CORS_ALLOWED_ORIGINS`: comma-separated allowed frontend origins

Operational rules:

- `JWT_SECRET_KEY` is required. Do not use a placeholder or short string. Use a long random secret and manage it as a deployment secret.
- `DB_ECHO` should stay `false` outside local debugging, otherwise SQL and bound values may leak into logs.
- `CORS_ALLOWED_ORIGINS` must be environment-driven. For local development, a value such as `http://localhost:3000,http://127.0.0.1:3000` is acceptable. In deployment, replace it with the real frontend origin list.
- Do not commit a real `.env` file. Commit `.env.example` only.

## API Surface

The main router is mounted under `/api/v1`.

Current top-level route groups:

- public and admin post APIs
- user APIs
- category APIs
- tag APIs
- site setting / public site-config APIs
- admin aggregate APIs

Public and admin responsibilities are intentionally split. Admin write endpoints under `/api/v1/admin/...` are expected to be admin-only, while public read endpoints stay on the public surface.

## Development Commands

Install dependencies:

```powershell
uv sync
```

Run the development server:

```powershell
uv run uvicorn app.main:app --reload
```

Run the default test suite:

```powershell
uv run pytest -q
```

## Database Migrations

Apply the latest schema:

```powershell
uv run alembic upgrade head
```

Create a new migration after model changes:

```powershell
uv run alembic revision --autogenerate -m "describe_change"
```

Generate SQL without applying it:

```powershell
uv run alembic upgrade head --sql
```

`mysql.sql` can still be used as a manual bootstrap snapshot, but Alembic is the primary path for schema evolution.

## Health And Observability

- `/health/live`: process liveness only
- `/health/ready`: dependency readiness, currently includes database availability
- `/health`: alias to readiness

The service uses structured logging plus request logging middleware. Startup does not fail hard when the database is temporarily unavailable; readiness reports dependency state instead.

## Testing

The default suite is fast and mock-friendly:

```powershell
uv run pytest -q
```

### Integration Smoke Tests

Real database integration tests are opt-in.

Create an empty MySQL database for integration testing, set `INTEGRATION_DATABASE_URL`, and run:

```powershell
$env:INTEGRATION_DATABASE_URL = "mysql+aiomysql://user:password@127.0.0.1:3306/xiaobaicai_integration?charset=utf8mb4"
uv run pytest tests/test_integration_smoke.py -q
```

Those tests will:

- run Alembic migrations against the target database
- verify core tables exist after upgrade
- insert real data through command services
- verify core public post behavior against a real database

If Alembic must target a different database URL during migration smoke runs, set `ALEMBIC_DATABASE_URL` as an override.
