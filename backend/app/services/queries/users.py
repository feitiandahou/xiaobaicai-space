from math import ceil
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_user_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import AuthenticationRequiredError, ConflictError, NotFoundError, PermissionDeniedError
from app.core.read_models import UserListPageReadModel, UserReadModel
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


def _apply_user_filters(stmt, *, search: str | None, is_active: bool | None, role: str | None):
    if search:
        keyword = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(keyword),
                User.email.ilike(keyword),
            )
        )
    if is_active is not None:
        stmt = stmt.where(User.is_active == int(is_active))
    if role is not None:
        stmt = stmt.where(User.role == role)
    return stmt


def _apply_user_sorting(
    stmt,
    *,
    sort_by: Literal["created_at", "updated_at", "username"],
    sort_order: Literal["asc", "desc"],
):
    sort_columns = {
        "created_at": User.created_at,
        "updated_at": User.updated_at,
        "username": User.username,
    }
    sort_column = sort_columns[sort_by]
    if sort_order == "asc":
        return stmt.order_by(sort_column.asc(), User.id.asc())
    return stmt.order_by(sort_column.desc(), User.id.desc())


async def list_users(
    db: AsyncSession,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    role: str | None = None,
    sort_by: Literal["created_at", "updated_at", "username"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    page_size: int = 10,
) -> UserListPageReadModel:
    stmt = _apply_user_sorting(
        _apply_user_filters(
            select(User),
            search=search,
            is_active=is_active,
            role=role,
        ),
        sort_by=sort_by,
        sort_order=sort_order,
    ).offset((page - 1) * page_size).limit(page_size)
    count_stmt = _apply_user_filters(select(func.count()).select_from(User), search=search, is_active=is_active, role=role)
    users = await db.scalars(stmt)
    total = int(await db.scalar(count_stmt) or 0)
    total_pages = ceil(total / page_size) if total > 0 else 0
    return UserListPageReadModel(
        data=[to_user_read_model(user) for user in users],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )


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