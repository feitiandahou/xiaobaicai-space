# Backend

## Environment

Create a `.env` file in the backend root. Use `.env.example` as the template.

## Install And Run

```powershell
uv sync
uv run uvicorn app.main:app --reload
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

`mysql.sql` can still be used as a manual bootstrap snapshot, but Alembic is now the primary path for schema evolution.

Do not commit the real `.env` file. Commit `.env.example` instead.
