from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT

from app.core.database import Base


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    admin_id = Column(BIGINT(unsigned=True), nullable=False)
    admin_name = Column(String(50))
    action = Column(String(50), nullable=False)
    detail = Column(Text)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500))
    os_info = Column(String(100))
    created_at = Column(DateTime, nullable=False, server_default=func.now())