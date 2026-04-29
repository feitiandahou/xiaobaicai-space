from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_models import AdminLogReadModel
from app.models.admin_log import AdminLog
from app.models.user import User
from app.schemas.admin_log import AdminLogCreate
from app.services.queries.admin_logs import ensure_admin_access, get_admin_log_record_or_raise
from app.assemblers import to_admin_log_read_model


async def record_admin_log(db: AsyncSession, payload: AdminLogCreate, *, actor: User) -> AdminLogReadModel:
    ensure_admin_access(actor)
    log = AdminLog(
        admin_id=int(actor.id),
        admin_name=getattr(actor, "username", None),
        action=payload.action,
        detail=payload.detail,
        ip_address=payload.ip_address,
        user_agent=payload.user_agent,
        os_info=payload.os_info,
    )
    db.add(log)
    await db.commit()
    created_log = await get_admin_log_record_or_raise(db, int(log.id))
    return to_admin_log_read_model(created_log)