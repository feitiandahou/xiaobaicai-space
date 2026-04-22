from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT

from app.core.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        server_onupdate=func.now(),
    )