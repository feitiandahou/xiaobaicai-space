from math import ceil

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_admin_log_read_model
from app.core.admin_actions import AdminAction
from app.core.error_codes import ErrorCode
from app.core.errors import NotFoundError, PermissionDeniedError, ValidationAppError
from app.core.read_models import AdminLogListPageReadModel, AdminLogReadModel
from app.models.admin_log import AdminLog
from app.models.user import User


class AdminLogQueryError(Exception):
    pass


class AdminLogNotFoundError(NotFoundError, AdminLogQueryError):
    code = ErrorCode.ADMIN_LOG_NOT_FOUND.value


class AdminLogPermissionError(PermissionDeniedError, AdminLogQueryError):
    code = ErrorCode.ADMIN_LOG_PERMISSION_DENIED.value


class AdminLogValidationError(ValidationAppError, AdminLogQueryError):
    pass


LogRangePreset = Literal["today", "last_7_days", "last_30_days", "all"]


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise AdminLogPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_admin_log_record_or_raise(db: AsyncSession, log_id: int) -> AdminLog:
    log = await db.get(AdminLog, log_id)
    if log is None:
        raise AdminLogNotFoundError(f"Admin log with id {log_id} not found")
    return log


def _apply_admin_log_filters(
    stmt,
    *,
    action: AdminAction | None,
    admin_id: int | None,
    detail_keyword: str | None,
    start_at: datetime | None,
    end_at: datetime | None,
):
    if start_at is not None and end_at is not None and start_at > end_at:
        raise AdminLogValidationError("start_at must be earlier than or equal to end_at")
    if action:
        stmt = stmt.where(AdminLog.action == action.value)
    if admin_id is not None:
        stmt = stmt.where(AdminLog.admin_id == admin_id)
    if detail_keyword:
        stmt = stmt.where(AdminLog.detail.ilike(f"%{detail_keyword.strip()}%"))
    if start_at is not None:
        stmt = stmt.where(AdminLog.created_at >= start_at)
    if end_at is not None:
        stmt = stmt.where(AdminLog.created_at <= end_at)
    return stmt


def _resolve_admin_log_range(
    *,
    range_preset: LogRangePreset,
    start_at: datetime | None,
    end_at: datetime | None,
) -> tuple[datetime | None, datetime | None]:
    if start_at is not None or end_at is not None:
        return start_at, end_at
    if range_preset == "all":
        return None, None

    now = datetime.now().replace(microsecond=0)
    if range_preset == "today":
        return now.replace(hour=0, minute=0, second=0), now
    if range_preset == "last_7_days":
        return now - timedelta(days=7), now
    return now - timedelta(days=30), now


async def list_admin_logs(
    db: AsyncSession,
    *,
    actor: User,
    action: AdminAction | None = None,
    admin_id: int | None = None,
    detail_keyword: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    range_preset: LogRangePreset = "last_30_days",
    page: int = 1,
    page_size: int = 20,
) -> AdminLogListPageReadModel:
    ensure_admin_access(actor)
    resolved_start_at, resolved_end_at = _resolve_admin_log_range(
        range_preset=range_preset,
        start_at=start_at,
        end_at=end_at,
    )
    stmt = _apply_admin_log_filters(
        select(AdminLog).order_by(AdminLog.created_at.desc(), AdminLog.id.desc()),
        action=action,
        admin_id=admin_id,
        detail_keyword=detail_keyword,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    ).offset((page - 1) * page_size).limit(page_size)
    count_stmt = _apply_admin_log_filters(
        select(func.count()).select_from(AdminLog),
        action=action,
        admin_id=admin_id,
        detail_keyword=detail_keyword,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    )
    logs = await db.scalars(stmt)
    total = int(await db.scalar(count_stmt) or 0)
    total_pages = ceil(total / page_size) if total > 0 else 0
    return AdminLogListPageReadModel(
        data=[to_admin_log_read_model(log) for log in logs],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )


async def get_admin_log(db: AsyncSession, log_id: int, *, actor: User) -> AdminLogReadModel:
    ensure_admin_access(actor)
    log = await get_admin_log_record_or_raise(db, log_id)
    return to_admin_log_read_model(log)