import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_setting_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.core.read_models import SettingReadModel, SiteConfigReadModel, SiteFooterReadModel, SiteLinkReadModel
from app.models.setting import Setting
from app.models.user import User


PUBLIC_SITE_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("site.title", "site_title"),
    "subtitle": ("site.subtitle", "site_subtitle"),
    "description": ("site.description", "site_description"),
    "icp_beian": ("site.icp_beian", "site_icp_beian"),
    "social_links": ("site.social_links", "social_links"),
    "footer_text": ("site.footer.text", "site_footer_text"),
    "footer_copyright": ("site.footer.copyright", "site_footer_copyright"),
    "footer_links": ("site.footer.links", "footer_links"),
}
PUBLIC_SITE_SETTING_KEYS = tuple(
    key
    for aliases in PUBLIC_SITE_SETTING_ALIASES.values()
    for key in aliases
)
DEFAULT_SITE_TITLE = "My Blog"


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


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _resolve_setting_value(
    settings_by_key: dict[str, Setting],
    aliases: tuple[str, ...],
) -> tuple[str | None, datetime | None]:
    for key in aliases:
        setting = settings_by_key.get(key)
        if setting is not None:
            return _normalize_optional_text(setting.value), setting.updated_at
    return None, None


def _parse_site_links(raw_value: str | None) -> list[SiteLinkReadModel]:
    if raw_value is None:
        return []

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    links: list[SiteLinkReadModel] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name_value = item.get("name")
        if not isinstance(name_value, str):
            name_value = item.get("label") if isinstance(item.get("label"), str) else None
        url_value = item.get("url") if isinstance(item.get("url"), str) else None
        icon_value = item.get("icon") if isinstance(item.get("icon"), str) else None

        name = _normalize_optional_text(name_value)
        url = _normalize_optional_text(url_value)
        icon = _normalize_optional_text(icon_value)
        if not name or not url:
            continue

        links.append(SiteLinkReadModel(name=name, url=url, icon=icon))

    return links


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


async def get_public_site_config(db: AsyncSession) -> SiteConfigReadModel:
    setting_rows = await db.scalars(select(Setting).where(Setting.key.in_(PUBLIC_SITE_SETTING_KEYS)).order_by(Setting.id.desc()))
    settings = list(setting_rows)
    settings_by_key = {setting.key: setting for setting in settings}

    title, title_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["title"])
    subtitle, subtitle_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["subtitle"])
    description, description_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["description"])
    icp_beian, icp_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["icp_beian"])
    social_links_value, social_links_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["social_links"])
    footer_text, footer_text_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["footer_text"])
    footer_copyright, footer_copyright_updated_at = _resolve_setting_value(
        settings_by_key,
        PUBLIC_SITE_SETTING_ALIASES["footer_copyright"],
    )
    footer_links_value, footer_links_updated_at = _resolve_setting_value(settings_by_key, PUBLIC_SITE_SETTING_ALIASES["footer_links"])

    updated_candidates = [
        title_updated_at,
        subtitle_updated_at,
        description_updated_at,
        icp_updated_at,
        social_links_updated_at,
        footer_text_updated_at,
        footer_copyright_updated_at,
        footer_links_updated_at,
    ]
    updated_at = max((value for value in updated_candidates if value is not None), default=None)

    return SiteConfigReadModel(
        title=title or DEFAULT_SITE_TITLE,
        subtitle=subtitle,
        description=description,
        icp_beian=icp_beian,
        social_links=_parse_site_links(social_links_value),
        footer=SiteFooterReadModel(
            text=footer_text,
            copyright=footer_copyright,
            links=_parse_site_links(footer_links_value),
        ),
        updated_at=updated_at,
    )