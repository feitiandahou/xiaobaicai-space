from sqlalchemy import JSON, Column, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
	__tablename__ = "users"

	id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
	username = Column(String(50), nullable=False, unique=True)
	password = Column(String(255), nullable=False)
	email = Column(String(100), unique=True)
	avatar = Column(String(255))
	bio = Column(Text)
	role = Column(String(20), nullable=False, default="user", server_default="user")
	social_links = Column(JSON)
	created_at = Column(DateTime, nullable=False, server_default=func.now())
	updated_at = Column(
		DateTime,
		nullable=False,
		server_default=func.now(),
		server_onupdate=func.now(),
	)

	posts = relationship("Post", back_populates="author")
