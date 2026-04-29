from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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