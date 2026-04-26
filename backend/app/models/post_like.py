from __future__ import annotations

from datetime import datetime
from sqlalchemy import  ForeignKey, Index, Nullable, UniqueConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.mysql import BIGINT
from app.core.database import Base


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "actor_key", name="uk_post_actor"),
        Index("idx_ip_created", "ip_address", "created_at"),
    )

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_key: Mapped[str] = mapped_column(String(80), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())