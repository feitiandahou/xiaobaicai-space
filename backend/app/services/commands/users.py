from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_user_read_model
from app.core.read_models import UserReadModel
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserCreate, UserStatusUpdate, UserUpdate
from app.services.commands.audit import AuditContext, record_admin_action
from app.services.queries.users import (
    UserAuthenticationError,
    UserConflictError,
    _ensure_can_access_user,
    _ensure_can_change_role,
    _ensure_can_manage_status,
    _ensure_user_is_active,
    _get_user_or_raise,
)
from app.utils.security import get_password_hash, verify_password


async def _ensure_username_available(
    db: AsyncSession,
    username: str,
    *,
    exclude_user_id: int | None = None,
) -> None:
    stmt = User.__table__.select().with_only_columns(User.id).where(User.username == username)
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

    stmt = User.__table__.select().with_only_columns(User.id).where(User.email == email)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    existing_user_id = await db.scalar(stmt)
    if existing_user_id is not None:
        raise UserConflictError(f"Email '{email}' is already in use")


async def create_user(db: AsyncSession, payload: UserCreate) -> UserReadModel:
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
    return to_user_read_model(created_user)


async def update_user(
    db: AsyncSession,
    user_id: int,
    payload: UserUpdate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> UserReadModel:
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
    user_read_model = to_user_read_model(updated_user)
    await record_admin_action(
        db,
        actor=actor,
        action="update_user",
        detail=f"Updated user {user_read_model.id} ({user_read_model.username})",
        audit_context=audit_context,
    )
    return user_read_model


async def change_password(
    db: AsyncSession,
    user_id: int,
    payload: ChangePasswordRequest,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
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
    await record_admin_action(
        db,
        actor=actor,
        action="change_password",
        detail=f"Changed password for user {user_id}",
        audit_context=audit_context,
    )


async def update_user_status(
    db: AsyncSession,
    user_id: int,
    payload: UserStatusUpdate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> UserReadModel:
    _ensure_can_manage_status(actor, user_id)
    user = await _get_user_or_raise(db, user_id)
    user.is_active = 1 if payload.is_active else 0

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UserConflictError("User status update failed") from exc

    updated_user = await _get_user_or_raise(db, user_id)
    user_read_model = to_user_read_model(updated_user)
    await record_admin_action(
        db,
        actor=actor,
        action="update_user_status",
        detail=f"Updated user status {user_read_model.id} ({user_read_model.username}) to is_active={user_read_model.is_active}",
        audit_context=audit_context,
    )
    return user_read_model