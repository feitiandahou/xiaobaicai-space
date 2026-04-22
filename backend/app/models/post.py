from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, Text, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, MEDIUMTEXT, TINYINT
from sqlalchemy.orm import relationship

from app.core.database import Base


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

	id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
	user_id = Column(BIGINT(unsigned=True), ForeignKey("users.id"), nullable=False)
	category_id = Column(
		BIGINT(unsigned=True),
		ForeignKey("categories.id", ondelete="SET NULL"),
	)
	title = Column(String(200), nullable=False)
	slug = Column(String(200), unique=True)
	summary = Column(String(500))
	content = Column(MEDIUMTEXT, nullable=False)
	cover_image = Column(String(255))
	status = Column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	is_delete = Column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	is_top = Column(
		TINYINT(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	view_count = Column(
		INTEGER(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	like_count = Column(
		INTEGER(unsigned=True),
		nullable=False,
		default=0,
		server_default="0",
	)
	published_at = Column(DateTime)
	created_at = Column(DateTime, nullable=False, server_default=func.now())
	updated_at = Column(
		DateTime,
		nullable=False,
		server_default=func.now(),
		server_onupdate=func.now(),
	)

	author = relationship("User", back_populates="posts")
	category = relationship("Category", back_populates="posts")
	tags = relationship("Tag", secondary=post_tags, back_populates="posts")