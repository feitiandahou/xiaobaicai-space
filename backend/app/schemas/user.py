from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_USER_ROLES = {"user", "admin"}


class UserPayloadBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名，长度 3-50")
    email: str | None = Field(default=None, max_length=100, description="邮箱地址")
    avatar: str | None = Field(default=None, max_length=255, description="头像URL")
    bio: str | None = Field(default=None, description="个人简介")
    social_links: dict[str, Any] = Field(default_factory=dict, description="社交链接")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if "@" not in value:
            raise ValueError("请输入有效的邮箱地址")
        return value


class UserCreate(UserPayloadBase):
    password: str = Field(..., min_length=6, max_length=128, description="密码，至少 6 位")


class UserLogin(BaseModel):
    account: str = Field(..., min_length=3, max_length=100, description="用户名或邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=100)
    avatar: str | None = Field(default=None, max_length=255)
    bio: str | None = None
    social_links: dict[str, Any] | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
    role: str | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if "@" not in value:
            raise ValueError("请输入有效的邮箱地址")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in ALLOWED_USER_ROLES:
            raise ValueError("role 必须是 user 或 admin")
        return value


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    avatar: str | None
    bio: str | None
    role: str
    is_active: bool
    social_links: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    data: UserOut


class UserListResponse(BaseModel):
    data: list[UserOut]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
