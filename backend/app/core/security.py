from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def create_access_token(*, user_id: int, expires_delta: timedelta | None = None) -> str:
	expire_at = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
	payload = {
		"sub": str(user_id),
		"exp": expire_at,
		"iat": datetime.now(UTC),
	}
	return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_access_token(token: str) -> int:
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
	except jwt.InvalidTokenError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc

	user_id = payload.get("sub")
	if user_id is None or not str(user_id).isdigit():
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"},
		)
	return int(user_id)


async def get_current_user(
	token: str = Depends(oauth2_scheme),
	db: AsyncSession = Depends(get_db),
) -> User:
	user_id = _decode_access_token(token)
	user = await db.get(User, user_id)
	if user is None or not bool(user.is_active):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authentication required",
			headers={"WWW-Authenticate": "Bearer"},
		)

	return user


def is_admin(user: User) -> bool:
	return user.role == "admin"


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
	if not is_admin(current_user):
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail="Admin access required",
		)

	return current_user
