from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    parent_id = Column(
        BIGINT(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
    )
    sort_order = Column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
    )
    icon = Column(String(100))
    status = Column(
        TINYINT(unsigned=True),
        nullable=False,
        default=1,
        server_default="1",
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    posts = relationship("Post", back_populates="category")