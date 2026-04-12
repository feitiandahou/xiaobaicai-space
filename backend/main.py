import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app = FastAPI()


def get_supabase_client() -> Client:
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY is not set. Add it to your environment or .env file.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def read_root():
    return {"message": "FastAPI with Supabase", "Supabase": "https://supabase.com/"}


@app.get("/test")
def list_test_rows():
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("test")
            .select("id,created_at,teststr")
            .order("id", desc=True)
            .limit(20)
            .execute()
        )
        return result.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/test")
def create_test_row(teststr: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("test")
            .insert({"teststr": teststr})
            .execute()
        )
        return result.data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))