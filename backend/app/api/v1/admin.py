from fastapi import APIRouter

from app.api.v1.posts import admin_router as admin_post_router
from app.api.v1.users import admin_router as admin_user_router


router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(admin_post_router)
router.include_router(admin_user_router)