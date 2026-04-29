from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import build_error_responses
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_admin_dashboard_response
from app.schemas.dashboard import AdminDashboardResponse
from app.services.queries.dashboard import get_admin_dashboard as get_admin_dashboard_service


admin_router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


@admin_router.get("", response_model=AdminDashboardResponse, responses=build_error_responses(401, 403))
async def get_admin_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AdminDashboardResponse:
    dashboard = await get_admin_dashboard_service(db, actor=current_user)
    return present_admin_dashboard_response(dashboard)