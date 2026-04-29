from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    parent_id: int = Field(default=0, ge=0)
    sort_order: int = Field(default=0, ge=0)
    icon: str | None = Field(default=None, max_length=100)
    status: int = Field(default=1, ge=0, le=1)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    slug: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    parent_id: int | None = Field(default=None, ge=0)
    sort_order: int | None = Field(default=None, ge=0)
    icon: str | None = Field(default=None, max_length=100)
    status: int | None = Field(default=None, ge=0, le=1)


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_count: int = 0
    created_at: datetime
    updated_at: datetime


class CategoryResponse(BaseModel):
    data: CategoryOut


class CategoryListResponse(BaseModel):
    data: list[CategoryOut]