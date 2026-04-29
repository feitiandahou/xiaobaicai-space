from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_setting_read_model
from app.core.read_models import SettingReadModel
from app.models.setting import Setting
from app.models.user import User
from app.services.commands.audit import AuditContext, record_admin_action
from app.services.queries.settings import SettingConflictError, ensure_admin_access, get_setting_record_or_raise


async def upsert_setting(
    db: AsyncSession,
    key: str,
    value: str | None,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> SettingReadModel:
    ensure_admin_access(actor)
    setting = await db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        setting = Setting(key=key, value=value)
        db.add(setting)
    else:
        setting.value = value

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise SettingConflictError("Setting update conflicts with existing data") from exc
    updated_setting = await get_setting_record_or_raise(db, key)
    setting_read_model = to_setting_read_model(updated_setting)
    await record_admin_action(
        db,
        actor=actor,
        action="upsert_setting",
        detail=f"Upserted setting {setting_read_model.key}",
        audit_context=audit_context,
    )
    return setting_read_model


async def delete_setting(
    db: AsyncSession,
    key: str,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> None:
    ensure_admin_access(actor)
    setting = await get_setting_record_or_raise(db, key)
    await db.delete(setting)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise SettingConflictError("Setting deletion failed") from exc
    await record_admin_action(
        db,
        actor=actor,
        action="delete_setting",
        detail=f"Deleted setting {key}",
        audit_context=audit_context,
    )