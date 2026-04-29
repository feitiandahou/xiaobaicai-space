from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_models import TagReadModel
from app.models.post import post_tags
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate
from app.services.commands.audit import AuditContext, record_admin_action
from app.services.queries.tags import (
    TagConflictError,
    build_tag_read_model,
    ensure_admin_access,
    get_tag_record_or_raise,
)


async def _ensure_name_available(db: AsyncSession, name: str, *, exclude_tag_id: int | None = None) -> None:
    stmt = select(Tag.id).where(Tag.name == name)
    if exclude_tag_id is not None:
        stmt = stmt.where(Tag.id != exclude_tag_id)
    existing_tag_id = await db.scalar(stmt)
    if existing_tag_id is not None:
        raise TagConflictError(f"Name '{name}' is already in use")


async def _ensure_slug_available(db: AsyncSession, slug: str, *, exclude_tag_id: int | None = None) -> None:
    stmt = select(Tag.id).where(Tag.slug == slug)
    if exclude_tag_id is not None:
        stmt = stmt.where(Tag.id != exclude_tag_id)
    existing_tag_id = await db.scalar(stmt)
    if existing_tag_id is not None:
        raise TagConflictError(f"Slug '{slug}' is already in use")


async def create_tag(
    db: AsyncSession,
    payload: TagCreate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> TagReadModel:
    ensure_admin_access(actor)
    await _ensure_name_available(db, payload.name)
    await _ensure_slug_available(db, payload.slug)

    tag = Tag(**payload.model_dump())
    db.add(tag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise TagConflictError("Tag already exists") from exc

    created_tag = await get_tag_record_or_raise(db, int(tag.id))
    tag_read_model = await build_tag_read_model(db, created_tag, published_only=False)
    await record_admin_action(
        db,
        actor=actor,
        action="create_tag",
        detail=f"Created tag {tag_read_model.id} ({tag_read_model.slug})",
        audit_context=audit_context,
    )
    return tag_read_model


async def update_tag(
    db: AsyncSession,
    tag_id: int,
    payload: TagUpdate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> TagReadModel:
    ensure_admin_access(actor)
    tag = await get_tag_record_or_raise(db, tag_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        await _ensure_name_available(db, update_data["name"], exclude_tag_id=tag_id)
    if "slug" in update_data:
        await _ensure_slug_available(db, update_data["slug"], exclude_tag_id=tag_id)

    for field_name, value in update_data.items():
        setattr(tag, field_name, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise TagConflictError("Tag update conflicts with existing data") from exc

    updated_tag = await get_tag_record_or_raise(db, tag_id)
    tag_read_model = await build_tag_read_model(db, updated_tag, published_only=False)
    await record_admin_action(
        db,
        actor=actor,
        action="update_tag",
        detail=f"Updated tag {tag_read_model.id} ({tag_read_model.slug})",
        audit_context=audit_context,
    )
    return tag_read_model


async def delete_tag(
    db: AsyncSession,
    tag_id: int,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> None:
    ensure_admin_access(actor)
    tag = await get_tag_record_or_raise(db, tag_id)
    post_count = await db.scalar(select(func.count()).select_from(post_tags).where(post_tags.c.tag_id == tag_id))
    if int(post_count or 0) > 0:
        raise TagConflictError("Tag is still referenced by posts")

    await db.delete(tag)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise TagConflictError("Tag deletion failed") from exc
    await record_admin_action(
        db,
        actor=actor,
        action="delete_tag",
        detail=f"Deleted tag {tag_id} ({tag.slug})",
        audit_context=audit_context,
    )