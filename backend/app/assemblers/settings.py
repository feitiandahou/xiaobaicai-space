from app.core.read_models import SettingReadModel
from app.models.setting import Setting


def to_setting_read_model(setting: Setting) -> SettingReadModel:
    return SettingReadModel(
        id=int(setting.id),
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at,
    )