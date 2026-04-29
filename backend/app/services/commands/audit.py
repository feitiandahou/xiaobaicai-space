from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.admin_log import AdminLogCreate
from app.services.commands.admin_logs import record_admin_log


@dataclass(slots=True, frozen=True)
class AuditContext:
    ip_address: str = "unknown"
    user_agent: str | None = None
    os_info: str | None = None


async def record_admin_action(
    db: AsyncSession,
    *,
    actor: User,
    action: str,
    detail: str,
    audit_context: AuditContext | None = None,
) -> None:
    if actor.role != "admin":
        return

    context = audit_context or AuditContext()
    payload = AdminLogCreate(
        action=action,
        detail=detail,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        os_info=context.os_info,
    )
    try:
        await record_admin_log(db, payload, actor=actor)
    except Exception:
        rollback = getattr(db, "rollback", None)
        if callable(rollback):
            try:
                await rollback()
            except Exception:
                pass