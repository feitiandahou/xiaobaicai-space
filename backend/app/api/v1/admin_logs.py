from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import build_error_responses
from app.core.admin_actions import AdminAction
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_admin_log_list_response, present_admin_log_out
from app.schemas.admin_log import AdminLogListResponse, AdminLogResponse
from app.services.queries.admin_logs import get_admin_log as get_admin_log_service, list_admin_logs as list_admin_logs_service


admin_router = APIRouter(prefix="/admin-logs", tags=["admin-logs"])


@admin_router.get("", response_model=AdminLogListResponse, responses=build_error_responses(401, 403, 422))
async def list_admin_logs(
    action: AdminAction | None = Query(None, description="Canonical admin action code"),
    admin_id: int | None = Query(None, ge=1),
    detail_keyword: str | None = Query(None, min_length=1, max_length=200),
    start_at: datetime | None = Query(None),
    end_at: datetime | None = Query(None),
    range_preset: Literal["today", "last_7_days", "last_30_days", "all"] = Query("last_30_days"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AdminLogListResponse:
    logs = await list_admin_logs_service(
        db,
        actor=current_user,
        action=action,
        admin_id=admin_id,
        detail_keyword=detail_keyword,
        start_at=start_at,
        end_at=end_at,
        range_preset=range_preset,
        page=page,
        page_size=page_size,
    )
    return present_admin_log_list_response(logs)


@admin_router.get("/{log_id}", response_model=AdminLogResponse, responses=build_error_responses(401, 403, 404, 422))
async def get_admin_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> AdminLogResponse:
    log = await get_admin_log_service(db, log_id, actor=current_user)
    return AdminLogResponse(data=present_admin_log_out(log))