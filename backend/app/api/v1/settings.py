from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import build_audit_context
from app.api.responses import build_error_responses
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_setting_list_response, present_setting_out
from app.schemas.post import MessageResponse
from app.schemas.setting import SettingListResponse, SettingResponse, SettingValueUpdate
from app.services.commands.settings import (
    delete_setting as delete_setting_service,
    upsert_setting as upsert_setting_service,
)
from app.services.queries.settings import (
    get_setting as get_setting_service,
    list_settings as list_settings_service,
)


admin_router = APIRouter(prefix="/settings", tags=["admin-settings"])


@admin_router.get("", response_model=SettingListResponse, responses=build_error_responses(401, 403))
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SettingListResponse:
    settings = await list_settings_service(db, actor=current_user)
    return present_setting_list_response(settings)


@admin_router.get("/{key}", response_model=SettingResponse, responses=build_error_responses(401, 403, 404))
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SettingResponse:
    setting = await get_setting_service(db, key, actor=current_user)
    return SettingResponse(data=present_setting_out(setting))


@admin_router.put("/{key}", response_model=SettingResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def upsert_setting(
    key: str,
    payload: SettingValueUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> SettingResponse:
    setting = await upsert_setting_service(db, key, payload.value, actor=current_user, audit_context=build_audit_context(request))
    return SettingResponse(data=present_setting_out(setting))


@admin_router.delete("/{key}", response_model=MessageResponse, responses=build_error_responses(401, 403, 404, 409))
async def delete_setting(
    key: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> MessageResponse:
    await delete_setting_service(db, key, actor=current_user, audit_context=build_audit_context(request))
    return MessageResponse(message="Setting deleted successfully")