from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
	from app.models.post import Post


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
	username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
	password: Mapped[str] = mapped_column(String(255), nullable=False)
	email: Mapped[str | None] = mapped_column(String(100), unique=True)
	avatar: Mapped[str | None] = mapped_column(String(255))
	bio: Mapped[str | None] = mapped_column(Text)
	role: Mapped[str] = mapped_column(String(20), nullable=False, default="user", server_default="user")
	is_active: Mapped[int] = mapped_column(
		TINYINT(unsigned=True),
		nullable=False,
		default=1,
		server_default="1",
	)
	social_links: Mapped[dict | list | None] = mapped_column(JSON)
	created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
	updated_at: Mapped[datetime] = mapped_column(
		DateTime,
		nullable=False,
		server_default=func.now(),
		server_onupdate=func.now(),
	)

	posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")
