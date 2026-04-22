from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.post import post_tags


class Tag(Base):
    __tablename__ = "tags"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    posts = relationship("Post", secondary=post_tags, back_populates="tags")