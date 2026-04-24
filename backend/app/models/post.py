from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, Text, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, MEDIUMTEXT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
	from app.models.category import Category
	from app.models.tag import Tag
	from app.models.user import User


post_tags = Table(
	"post_tags",
	Base.metadata,
	Column(
		"post_id",
		BIGINT(unsigned=True),
		ForeignKey("posts.id", ondelete="CASCADE"),
		primary_key=True,
	),
	Column(
		"tag_id",
		BIGINT(unsigned=True),
		ForeignKey("tags.id", ondelete="CASCADE"),
		primary_key=True,
	),
)


class Post(Base):
	__tablename__ = "posts"
	__table_args__ = (
		Index("idx_user_id", "user_id"),
		Index("idx_category_id", "category_id"),
		Index("idx_status_delete", "status", "is_delete"),
		Index("idx_published_at", "published_at"),
	)

	id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
	user_id: Mapped[int] = mapped_column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
	category_id: Mapped[int | None] = mapped_column(
		BIGINT(unsigned=True),
		ForeignKey("categories.id", ondelete="SET NULL"),
	)
	title: Mapped[str] = mapped_column(String(200), nullable=False)
	slug: Mapped[str | None] = mapped_column(String(200), unique=True)
	summary: Mapped[str | None] = mapped_column(String(500))
	content: Mapped[str] = mapped_column(MEDIUMTEXT, nullable=False)
	cover_image: Mapped[str | None] = mapped_column(String(255))
	status: Mapped[int] = mapped_column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	is_delete: Mapped[int] = mapped_column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	is_top: Mapped[int] = mapped_column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	view_count: Mapped[int] = mapped_column(
		INTEGER(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	like_count: Mapped[int] = mapped_column(
		INTEGER(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	published_at: Mapped[datetime | None] = mapped_column(DateTime)
	created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(
		DateTime,
		nullable=False,
		server_default=func.now(),
		server_onupdate=func.now(),
	)

	author: Mapped["User"] = relationship("User", back_populates="posts")
	category: Mapped["Category | None"] = relationship("Category", back_populates="posts")
	tags: Mapped[list["Tag"]] = relationship("Tag", secondary=post_tags, back_populates="posts")