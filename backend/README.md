# Backend

## Run with .env

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://aamxmeornrymixtkncxo.supabase.co
SUPABASE_KEY=your_publishable_or_service_role_key
```

Install dependencies and start the FastAPI app:

```powershell
uv sync
uv run uvicorn main:app --reload
```

Test endpoints:

```text
GET  http://127.0.0.1:8000/test
POST http://127.0.0.1:8000/test?teststr=hello
```

Do not commit the real `.env` file. Commit `.env.example` instead.
