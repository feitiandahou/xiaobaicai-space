from typing import Optional, List, Dict, Any
from pydantic import BaseModel,  Field, field_validator, ConfigDict
from datetime import datetime
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名，长度 3-50")
    #可选字段
    email: Optional[str] = Field(None, description="邮箱地址")
    avatar: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    role: Optional[str] = Field("user", description="用户角色，默认为 user")
    social_links: Optional[Dict[str, Any]] = Field(default_factory=dict, description="社交链接")

    #自定义校验：比如检查邮箱格式
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError('请输入有效的邮箱地址')
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="密码，至少 6 位")
class UserUpdate(BaseModel):
    # 继承后 可以覆盖特定字段
    username: Optional[str] = None
    email: Optional[str] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    #数据库自动生成， 请求不需要填，但是响应需要拿值
    id: int
    created_at: datetime
    updated_at: datetime
