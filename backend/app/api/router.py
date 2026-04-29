from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.categories import router as category_router
from app.api.v1.posts import router as post_router
from app.api.v1.tags import router as tag_router
from app.api.v1.users import router as user_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(admin_router)
api_router.include_router(category_router)
api_router.include_router(post_router)
api_router.include_router(tag_router)
api_router.include_router(user_router)