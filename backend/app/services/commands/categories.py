from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.read_models import CategoryReadModel
from app.models.category import Category
from app.models.post import Post
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.commands.audit import AuditContext, record_admin_action
from app.services.queries.categories import (
    CategoryConflictError,
    CategoryValidationError,
    build_category_read_model,
    ensure_admin_access,
    get_category_record_or_raise,
)


async def _ensure_slug_available(
    db: AsyncSession,
    slug: str,
    *,
    exclude_category_id: int | None = None,
) -> None:
    stmt = select(Category.id).where(Category.slug == slug)
    if exclude_category_id is not None:
        stmt = stmt.where(Category.id != exclude_category_id)
    existing_category_id = await db.scalar(stmt)
    if existing_category_id is not None:
        raise CategoryConflictError(f"Slug '{slug}' is already in use")


async def _ensure_parent_exists(db: AsyncSession, parent_id: int) -> None:
    if parent_id == 0:
        return
    parent = await db.get(Category, parent_id)
    if parent is None:
        raise CategoryValidationError(f"Parent category with id {parent_id} does not exist")


async def create_category(
    db: AsyncSession,
    payload: CategoryCreate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> CategoryReadModel:
    ensure_admin_access(actor)
    await _ensure_slug_available(db, payload.slug)
    await _ensure_parent_exists(db, payload.parent_id)

    category = Category(**payload.model_dump())
    db.add(category)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise CategoryConflictError("Category already exists") from exc

    created_category = await get_category_record_or_raise(db, int(category.id))
    category_read_model = await build_category_read_model(db, created_category, published_only=False)
    await record_admin_action(
        db,
        actor=actor,
        action="create_category",
        detail=f"Created category {category_read_model.id} ({category_read_model.slug})",
        audit_context=audit_context,
    )
    return category_read_model


async def update_category(
    db: AsyncSession,
    category_id: int,
    payload: CategoryUpdate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> CategoryReadModel:
    ensure_admin_access(actor)
    category = await get_category_record_or_raise(db, category_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "slug" in update_data:
        await _ensure_slug_available(db, update_data["slug"], exclude_category_id=category_id)
    if "parent_id" in update_data:
        parent_id = update_data["parent_id"]
        if parent_id == category_id:
            raise CategoryValidationError("Category cannot be its own parent")
        await _ensure_parent_exists(db, parent_id)

    for field_name, value in update_data.items():
        setattr(category, field_name, value)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise CategoryConflictError("Category update conflicts with existing data") from exc

    updated_category = await get_category_record_or_raise(db, category_id)
    category_read_model = await build_category_read_model(db, updated_category, published_only=False)
    await record_admin_action(
        db,
        actor=actor,
        action="update_category",
        detail=f"Updated category {category_read_model.id} ({category_read_model.slug})",
        audit_context=audit_context,
    )
    return category_read_model


async def delete_category(
    db: AsyncSession,
    category_id: int,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> None:
    ensure_admin_access(actor)
    category = await get_category_record_or_raise(db, category_id)

    child_count = await db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == category_id))
    if int(child_count or 0) > 0:
        raise CategoryConflictError("Category has child categories")

    post_count = await db.scalar(select(func.count()).select_from(Post).where(Post.category_id == category_id, Post.is_delete == 0))
    if int(post_count or 0) > 0:
        raise CategoryConflictError("Category is still referenced by posts")

    await db.delete(category)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise CategoryConflictError("Category deletion failed") from exc
    await record_admin_action(
        db,
        actor=actor,
        action="delete_category",
        detail=f"Deleted category {category_id} ({category.slug})",
        audit_context=audit_context,
    )