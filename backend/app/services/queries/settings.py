from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_setting_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.core.read_models import SettingReadModel
from app.models.setting import Setting
from app.models.user import User


class SettingQueryError(Exception):
    pass


class SettingNotFoundError(NotFoundError, SettingQueryError):
    code = ErrorCode.SETTING_NOT_FOUND.value


class SettingConflictError(ConflictError, SettingQueryError):
    code = ErrorCode.SETTING_CONFLICT.value


class SettingPermissionError(PermissionDeniedError, SettingQueryError):
    code = ErrorCode.SETTING_PERMISSION_DENIED.value


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise SettingPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_setting_record_or_raise(db: AsyncSession, key: str) -> Setting:
    setting = await db.scalar(select(Setting).where(Setting.key == key))
    if setting is None:
        raise SettingNotFoundError(f"Setting with key '{key}' not found")
    return setting


async def list_settings(db: AsyncSession, *, actor: User) -> list[SettingReadModel]:
    ensure_admin_access(actor)
    settings = await db.scalars(select(Setting).order_by(Setting.key.asc(), Setting.id.asc()))
    return [to_setting_read_model(setting) for setting in settings]


async def get_setting(db: AsyncSession, key: str, *, actor: User) -> SettingReadModel:
    ensure_admin_access(actor)
    setting = await get_setting_record_or_raise(db, key)
    return to_setting_read_model(setting)