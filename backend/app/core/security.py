from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.error_codes import ErrorCode
from app.core.errors import AuthenticationRequiredError, PermissionDeniedError
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login", auto_error=False)


def create_access_token(*, user_id: int, expires_delta: timedelta | None = None) -> str:
	expire_at = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
	payload = {
		"sub": str(user_id),
		"exp": expire_at,
		"iat": datetime.now(UTC),
	}
	return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def _get_bearer_token(token: str | None = Depends(oauth2_scheme)) -> str:
	if not token:
		raise AuthenticationRequiredError("Authentication required")
	return token


def _decode_access_token(token: str) -> int:
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
	except jwt.InvalidTokenError as exc:
		raise AuthenticationRequiredError("Invalid or expired token", code=ErrorCode.INVALID_TOKEN.value) from exc

	user_id = payload.get("sub")
	if user_id is None or not str(user_id).isdigit():
		raise AuthenticationRequiredError("Invalid or expired token", code=ErrorCode.INVALID_TOKEN.value)
	return int(user_id)


async def get_current_user(
	token: str = Depends(_get_bearer_token),
	db: AsyncSession = Depends(get_db),
) -> User:
	user_id = _decode_access_token(token)
	user = await db.get(User, user_id)
	if user is None or not bool(user.is_active):
		raise AuthenticationRequiredError("Authentication required")

	return user


def is_admin(user: User) -> bool:
	return user.role == "admin"


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
	if not is_admin(current_user):
		raise PermissionDeniedError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)

	return current_user
