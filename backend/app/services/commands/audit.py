from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_actions import AdminAction
from app.core.observability import get_logger
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
    action: AdminAction,
    detail: str,
    audit_context: AuditContext | None = None,
    actor_role_override: str | None = None,
) -> None:
    effective_actor_role = actor_role_override or actor.role
    if effective_actor_role != "admin":
        return

    context = audit_context or AuditContext()
    logger = get_logger(__name__)
    payload = AdminLogCreate(
        action=action,
        detail=detail,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        os_info=context.os_info,
    )
    logger.info(
        "admin_audit_record_requested",
        extra={
            "event": "admin_audit_record_requested",
            "actor_id": int(actor.id),
            "action": action.value,
            "detail": detail,
            "ip_address": context.ip_address,
        },
    )
    try:
        await record_admin_log(db, payload, actor=actor)
        logger.info(
            "admin_audit_recorded",
            extra={
                "event": "admin_audit_recorded",
                "actor_id": int(actor.id),
                "action": action.value,
                "detail": detail,
            },
        )
    except Exception:
        logger.exception(
            "admin_audit_failed",
            extra={
                "event": "admin_audit_failed",
                "actor_id": int(actor.id),
                "action": action.value,
                "detail": detail,
            },
        )
        rollback = cast(Callable[[], Awaitable[None]] | None, getattr(db, "rollback", None))
        if callable(rollback):
            try:
                await rollback()
            except Exception:
                pass