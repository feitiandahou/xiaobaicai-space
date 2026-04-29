from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_codes import ErrorCode
from app.core.errors import (
    AuthenticationRequiredError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserCreate, UserStatusUpdate, UserUpdate
from app.utils.security import get_password_hash, verify_password


class UserServiceError(Exception):
    pass


class UserNotFoundError(NotFoundError, UserServiceError):
    code = ErrorCode.USER_NOT_FOUND.value
    pass


class UserConflictError(ConflictError, UserServiceError):
    code = ErrorCode.USER_CONFLICT.value
    pass


class UserPermissionError(PermissionDeniedError, UserServiceError):
    code = ErrorCode.USER_PERMISSION_DENIED.value
    pass


class UserAuthenticationError(AuthenticationRequiredError, UserServiceError):
    code = ErrorCode.USER_AUTHENTICATION_FAILED.value
    pass


class UserInactiveError(PermissionDeniedError, UserServiceError):
    code = ErrorCode.USER_INACTIVE.value
    pass


def _is_admin(actor: User) -> bool:
    return actor.role == "admin"


async def _get_user_or_raise(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User with id {user_id} not found")
    return user


async def _ensure_username_available(
    db: AsyncSession,
    username: str,
    *,
    exclude_user_id: int | None = None,
) -> None:
    stmt = select(User.id).where(User.username == username)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    existing_user_id = await db.scalar(stmt)
    if existing_user_id is not None:
        raise UserConflictError(f"Username '{username}' is already in use")


async def _ensure_email_available(
    db: AsyncSession,
    email: str | None,
    *,
    exclude_user_id: int | None = None,
) -> None:
    if email is None:
        return

    stmt = select(User.id).where(User.email == email)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    existing_user_id = await db.scalar(stmt)
    if existing_user_id is not None:
        raise UserConflictError(f"Email '{email}' is already in use")


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


async def _get_user_by_account_or_raise(db: AsyncSession, account: str) -> User:
    stmt = select(User).where(or_(User.username == account, User.email == account))
    user = await db.scalar(stmt)
    if user is None:
        raise UserAuthenticationError("Invalid credentials")
    return user


async def list_users(db: AsyncSession) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
    users = await db.scalars(stmt)
    return list(users)


async def get_user(db: AsyncSession, user_id: int, *, actor: User) -> User:
    _ensure_can_access_user(actor, user_id)
    user = await _get_user_or_raise(db, user_id)
    return user


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    await _ensure_username_available(db, payload.username)
    await _ensure_email_available(db, payload.email)

    user = User(
        username=payload.username,
        email=payload.email,
        avatar=payload.avatar,
        bio=payload.bio,
        social_links=payload.social_links,
        password=get_password_hash(payload.password),
        role="user",
        is_active=1,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UserConflictError("User already exists") from exc

    created_user = await _get_user_or_raise(db, int(user.id))
    return created_user


async def update_user(db: AsyncSession, user_id: int, payload: UserUpdate, *, actor: User) -> User:
    _ensure_can_access_user(actor, user_id)
    user = await _get_user_or_raise(db, user_id)

    update_data = payload.model_dump(exclude_unset=True)

    if "role" in update_data:
        _ensure_can_change_role(actor)
    if "username" in update_data:
        await _ensure_username_available(db, update_data["username"], exclude_user_id=user_id)
    if "email" in update_data:
        await _ensure_email_available(db, update_data["email"], exclude_user_id=user_id)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])

    for field_name, value in update_data.items():
        setattr(user, field_name, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UserConflictError("User update conflicts with existing data") from exc

    updated_user = await _get_user_or_raise(db, user_id)
    return updated_user


async def authenticate_user(db: AsyncSession, account: str, password: str) -> User:
    user = await _get_user_by_account_or_raise(db, account)
    _ensure_user_is_active(user)
    if not verify_password(password, user.password):
        raise UserAuthenticationError("Invalid credentials")
    return user


async def change_password(
    db: AsyncSession,
    user_id: int,
    payload: ChangePasswordRequest,
    *,
    actor: User,
) -> None:
    _ensure_can_access_user(actor, user_id)
    user = await _get_user_or_raise(db, user_id)
    _ensure_user_is_active(user)

    if not verify_password(payload.current_password, user.password):
        raise UserAuthenticationError("Current password is incorrect")
    if payload.current_password == payload.new_password:
        raise UserConflictError("New password must be different from current password")

    user.password = get_password_hash(payload.new_password)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UserConflictError("Password update failed") from exc


async def update_user_status(
    db: AsyncSession,
    user_id: int,
    payload: UserStatusUpdate,
    *,
    actor: User,
) -> User:
    _ensure_can_manage_status(actor, user_id)
    user = await _get_user_or_raise(db, user_id)
    user.is_active = 1 if payload.is_active else 0

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UserConflictError("User status update failed") from exc

    updated_user = await _get_user_or_raise(db, user_id)
    return updated_user