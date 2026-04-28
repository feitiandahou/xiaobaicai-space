from fastapi import APIRouter

from app.api.v1.posts import router as post_router
from app.api.v1.users import router as user_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(post_router)
api_router.include_router(user_router)