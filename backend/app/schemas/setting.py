from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


def _default_site_footer() -> "SiteFooterOut":
    return SiteFooterOut(text=None, copyright=None, links=[])


class SettingValueUpdate(BaseModel):
    value: str | None = None


class SettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str = Field(..., min_length=1, max_length=100)
    value: str | None = None
    updated_at: datetime


class SettingResponse(BaseModel):
    data: SettingOut


class SettingListResponse(BaseModel):
    data: list[SettingOut]


class SiteLinkOut(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    icon: str | None = Field(None, max_length=100)


class SiteFooterOut(BaseModel):
    text: str | None = Field(None, max_length=500)
    copyright: str | None = Field(None, max_length=200)
    links: list[SiteLinkOut] = Field(default_factory=list)


class SiteConfigOut(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    subtitle: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=500)
    icp_beian: str | None = Field(None, max_length=100)
    social_links: list[SiteLinkOut] = Field(default_factory=list)
    footer: SiteFooterOut = Field(default_factory=_default_site_footer)
    updated_at: datetime | None = None


class SiteConfigResponse(BaseModel):
    data: SiteConfigOut