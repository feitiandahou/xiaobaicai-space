from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import build_error_responses
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_admin_log_list_response, present_admin_log_out
from app.schemas.admin_log import AdminLogListResponse, AdminLogResponse
from app.services.queries.admin_logs import get_admin_log as get_admin_log_service, list_admin_logs as list_admin_logs_service


admin_router = APIRouter(prefix="/admin-logs", tags=["admin-logs"])


@admin_router.get("", response_model=AdminLogListResponse, responses=build_error_responses(401, 403))
async def list_admin_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AdminLogListResponse:
    logs = await list_admin_logs_service(db, actor=current_user)
    return present_admin_log_list_response(logs)


@admin_router.get("/{log_id}", response_model=AdminLogResponse, responses=build_error_responses(401, 403, 404, 422))
async def get_admin_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AdminLogResponse:
    log = await get_admin_log_service(db, log_id, actor=current_user)
    return AdminLogResponse(data=present_admin_log_out(log))