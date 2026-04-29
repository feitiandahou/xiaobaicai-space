from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_admin_log_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import NotFoundError, PermissionDeniedError
from app.core.read_models import AdminLogReadModel
from app.models.admin_log import AdminLog
from app.models.user import User


class AdminLogQueryError(Exception):
    pass


class AdminLogNotFoundError(NotFoundError, AdminLogQueryError):
    code = ErrorCode.ADMIN_LOG_NOT_FOUND.value


class AdminLogPermissionError(PermissionDeniedError, AdminLogQueryError):
    code = ErrorCode.ADMIN_LOG_PERMISSION_DENIED.value


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise AdminLogPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_admin_log_record_or_raise(db: AsyncSession, log_id: int) -> AdminLog:
    log = await db.get(AdminLog, log_id)
    if log is None:
        raise AdminLogNotFoundError(f"Admin log with id {log_id} not found")
    return log


async def list_admin_logs(db: AsyncSession, *, actor: User) -> list[AdminLogReadModel]:
    ensure_admin_access(actor)
    logs = await db.scalars(select(AdminLog).order_by(AdminLog.created_at.desc(), AdminLog.id.desc()))
    return [to_admin_log_read_model(log) for log in logs]


async def get_admin_log(db: AsyncSession, log_id: int, *, actor: User) -> AdminLogReadModel:
    ensure_admin_access(actor)
    log = await get_admin_log_record_or_raise(db, log_id)
    return to_admin_log_read_model(log)