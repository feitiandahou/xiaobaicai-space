from app.core.read_models import SettingReadModel, SiteConfigReadModel, SiteFooterReadModel, SiteLinkReadModel
from app.schemas.setting import SettingListResponse, SettingOut, SiteConfigOut, SiteConfigResponse, SiteFooterOut, SiteLinkOut


def present_setting_out(setting: SettingReadModel) -> SettingOut:
    return SettingOut(
        id=int(setting.id),
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at,
    )


def present_setting_list_response(settings: list[SettingReadModel]) -> SettingListResponse:
    return SettingListResponse(data=[present_setting_out(setting) for setting in settings])


def present_site_link_out(link: SiteLinkReadModel) -> SiteLinkOut:
    return SiteLinkOut(name=link.name, url=link.url, icon=link.icon)


def present_site_footer_out(footer: SiteFooterReadModel) -> SiteFooterOut:
    return SiteFooterOut(
        text=footer.text,
        copyright=footer.copyright,
        links=[present_site_link_out(link) for link in footer.links],
    )


def present_site_config_out(config: SiteConfigReadModel) -> SiteConfigOut:
    return SiteConfigOut(
        title=config.title,
        subtitle=config.subtitle,
        description=config.description,
        icp_beian=config.icp_beian,
        social_links=[present_site_link_out(link) for link in config.social_links],
        footer=present_site_footer_out(config.footer),
        updated_at=config.updated_at,
    )


def present_site_config_response(config: SiteConfigReadModel) -> SiteConfigResponse:
    return SiteConfigResponse(data=present_site_config_out(config))