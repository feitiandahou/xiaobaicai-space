from app.core.read_models import SettingReadModel
from app.schemas.setting import SettingListResponse, SettingOut


def present_setting_out(setting: SettingReadModel) -> SettingOut:
    return SettingOut(
        id=int(setting.id),
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at,
    )


def present_setting_list_response(settings: list[SettingReadModel]) -> SettingListResponse:
    return SettingListResponse(data=[present_setting_out(setting) for setting in settings])