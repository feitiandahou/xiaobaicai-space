from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
	title: str = Field(..., max_length=200, description="文章标题")
	slug: str | None = Field(default=None, max_length=200, description="URL 标识")
	summary: str | None = Field(default=None, max_length=500, description="文章摘要")
	content: str = Field(..., description="文章正文")
	cover_image: str | None = Field(default=None, max_length=255, description="封面图")
	category_id: int | None = Field(default=None, description="分类 ID")
	status: int = Field(default=0, ge=0, le=2, description="状态: 0 草稿, 1 已发布, 2 已归档")
	is_top: int = Field(default=0, ge=0, le=1, description="是否置顶")
	published_at: datetime | None = Field(default=None, description="发布时间")


class PostCreate(PostBase):
	user_id: int = Field(..., description="作者 ID")
	tag_ids: list[int] = Field(default_factory=list, description="标签 ID 列表")


class PostUpdate(BaseModel):
	title: str | None = Field(default=None, max_length=200)
	slug: str | None = Field(default=None, max_length=200)
	summary: str | None = Field(default=None, max_length=500)
	content: str | None = None
	cover_image: str | None = Field(default=None, max_length=255)
	category_id: int | None = None
	status: int | None = Field(default=None, ge=0, le=2)
	is_top: int | None = Field(default=None, ge=0, le=1)
	is_delete: int | None = Field(default=None, ge=0, le=1)
	published_at: datetime | None = None
	tag_ids: list[int] | None = None


class PostOut(PostBase):
	model_config = ConfigDict(from_attributes=True)

	id: int
	user_id: int
	is_delete: int
	view_count: int
	like_count: int
	created_at: datetime
	updated_at: datetime
	tag_ids: list[int] = Field(default_factory=list)
	tags: list[str] = Field(default_factory=list)


class PostListItem(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	title: str
	slug: str | None
	summary: str | None
	cover_image: str | None
	status: int
	is_top: int
	view_count: int
	like_count: int
	published_at: datetime | None
	created_at: datetime
	tag_ids: list[int] = Field(default_factory=list)
	tags: list[str] = Field(default_factory=list)


class PostResponse(BaseModel):
	data: PostOut


class PostListResponse(BaseModel):
	data: list[PostListItem]


class PostLikeResponse(BaseModel):
	message: str
	like_count: int


class MessageResponse(BaseModel):
	message: str

