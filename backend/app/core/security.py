from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User


async def get_current_user(
	x_user_id: int | None = Header(default=None, alias="X-User-Id"),
	db: AsyncSession = Depends(get_db),
) -> User:
	if x_user_id is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authentication required",
		)

	user = await db.get(User, x_user_id)
	if user is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authentication required",
		)

	return user
