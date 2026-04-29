from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    slug: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    slug: str | None = Field(default=None, min_length=1, max_length=50)


class TagOut(TagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_count: int = 0
    created_at: datetime


class TagResponse(BaseModel):
    data: TagOut


class TagListResponse(BaseModel):
    data: list[TagOut]