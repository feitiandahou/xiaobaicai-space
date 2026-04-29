from fastapi import APIRouter

from app.api.v1.admin_logs import admin_router as admin_log_router
from app.api.v1.categories import admin_router as admin_category_router
from app.api.v1.posts import admin_router as admin_post_router
from app.api.v1.settings import admin_router as admin_setting_router
from app.api.v1.tags import admin_router as admin_tag_router
from app.api.v1.users import admin_router as admin_user_router


router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(admin_log_router)
router.include_router(admin_category_router)
router.include_router(admin_post_router)
router.include_router(admin_setting_router)
router.include_router(admin_tag_router)
router.include_router(admin_user_router)