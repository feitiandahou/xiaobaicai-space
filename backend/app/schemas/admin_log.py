from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.admin_actions import AdminAction


class AdminLogCreate(BaseModel):
    action: AdminAction = Field(..., description="Canonical admin action code")
    detail: str | None = None
    ip_address: str = Field(..., min_length=1, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)
    os_info: str | None = Field(default=None, max_length=100)


class AdminLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admin_id: int
    admin_name: str | None
    action: str
    detail: str | None
    ip_address: str
    user_agent: str | None
    os_info: str | None
    created_at: datetime


class AdminLogResponse(BaseModel):
    data: AdminLogOut


class AdminLogListMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class AdminLogListResponse(BaseModel):
    data: list[AdminLogOut]
    meta: AdminLogListMeta