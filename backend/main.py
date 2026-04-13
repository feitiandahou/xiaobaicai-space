import os
from typing import Optional, List
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from supabase import Client, create_client
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "default-admin-token-change-in-prod")

app = FastAPI(title="Xiaobaicai Space Blog API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_supabase_client() -> Client:
    if not SUPABASE_KEY or not SUPABASE_URL:
        raise RuntimeError("SUPABASE_KEY or SUPABASE_URL is not set.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Dependency for Admin auth
def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden. Invalid Admin Token.")
    return True

# --- Pydantic Models ---
class PostCreate(BaseModel):
    title: str
    slug: str
    summary: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    is_published: bool = False

class PostUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    is_published: Optional[bool] = None

# --- Public Endpoints ---
@app.get("/api/posts")
def get_published_posts():
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("posts")
            .select("id, title, slug, summary, cover_image, created_at, likes")
            .eq("is_published", True)
            .order("created_at", desc=True)
            .execute()
        )
        return {"data": result.data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/posts/{slug}")
def get_post_by_slug(slug: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("posts")
            .select("*")
            .eq("slug", slug)
            .eq("is_published", True)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"data": result.data[0]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/posts/{slug}/like")
def like_post(slug: str):
    try:
        supabase = get_supabase_client()
        # First get the post
        post_result = supabase.table("posts").select("id, likes").eq("slug", slug).execute()
        if not post_result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_id = post_result.data[0]["id"]
        current_likes = post_result.data[0].get("likes", 0)
        
        # Increment likes
        update_result = (
            supabase.table("posts")
            .update({"likes": current_likes + 1})
            .eq("id", post_id)
            .execute()
        )
        return {"message": "Liked successfully", "likes": update_result.data[0]["likes"]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# --- Admin Endpoints ---
@app.get("/api/admin/posts", dependencies=[Depends(verify_admin)])
def get_all_posts_admin():
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("posts")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return {"data": result.data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/admin/posts", dependencies=[Depends(verify_admin)])
def create_post(post: PostCreate):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("posts")
            .insert(post.model_dump())
            .execute()
        )
        return {"message": "Post created", "data": result.data[0]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.put("/api/admin/posts/{id}", dependencies=[Depends(verify_admin)])
def update_post(id: str, post: PostUpdate):
    try:
        supabase = get_supabase_client()
        update_data = {k: v for k, v in post.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = (
            supabase.table("posts")
            .update(update_data)
            .eq("id", id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post updated", "data": result.data[0]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.delete("/api/admin/posts/{id}", dependencies=[Depends(verify_admin)])
def delete_post(id: str):
    try:
        supabase = get_supabase_client()
        result = (
            supabase.table("posts")
            .delete()
            .eq("id", id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))