from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_user_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import AuthenticationRequiredError, ConflictError, NotFoundError, PermissionDeniedError
from app.core.read_models import UserReadModel
from app.models.user import User
from app.utils.security import verify_password


class UserQueryError(Exception):
    pass


class UserNotFoundError(NotFoundError, UserQueryError):
    code = ErrorCode.USER_NOT_FOUND.value


class UserConflictError(ConflictError, UserQueryError):
    code = ErrorCode.USER_CONFLICT.value


class UserPermissionError(PermissionDeniedError, UserQueryError):
    code = ErrorCode.USER_PERMISSION_DENIED.value


class UserAuthenticationError(AuthenticationRequiredError, UserQueryError):
    code = ErrorCode.USER_AUTHENTICATION_FAILED.value


class UserInactiveError(PermissionDeniedError, UserQueryError):
    code = ErrorCode.USER_INACTIVE.value


def _is_admin(actor: User) -> bool:
    return actor.role == "admin"


def _ensure_can_access_user(actor: User, target_user_id: int) -> None:
    if _is_admin(actor):
        return
    if int(actor.id) != target_user_id:
        raise UserPermissionError("Not allowed to access this user")


def _ensure_can_change_role(actor: User) -> None:
    if not _is_admin(actor):
        raise UserPermissionError("Only admin can change user role")


def _ensure_user_is_active(user: User) -> None:
    if not bool(user.is_active):
        raise UserInactiveError("User account is disabled")


def _ensure_can_manage_status(actor: User, target_user_id: int) -> None:
    if not _is_admin(actor):
        raise UserPermissionError("Only admin can change user status")
    if int(actor.id) == target_user_id:
        raise UserPermissionError("Admin cannot disable current account")


async def _get_user_or_raise(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with id {user_id} not found")
    return user


async def _get_user_by_account_or_raise(db: AsyncSession, account: str) -> User:
    stmt = select(User).where(or_(User.username == account, User.email == account))
    user = await db.scalar(stmt)
    if user is None:
        raise UserAuthenticationError("Invalid credentials")
    return user


async def list_users(db: AsyncSession) -> list[UserReadModel]:
    users = await db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc()))
    return [to_user_read_model(user) for user in users]


async def get_user(db: AsyncSession, user_id: int, *, actor: User) -> UserReadModel:
    _ensure_can_access_user(actor, user_id)
    user = await _get_user_or_raise(db, user_id)
    return to_user_read_model(user)


async def authenticate_user(db: AsyncSession, account: str, password: str) -> UserReadModel:
    user = await _get_user_by_account_or_raise(db, account)
    _ensure_user_is_active(user)
    if not verify_password(password, user.password):
        raise UserAuthenticationError("Invalid credentials")
    return to_user_read_model(user)