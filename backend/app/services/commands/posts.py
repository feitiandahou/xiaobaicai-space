from collections.abc import Sequence
import re

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_post_read_model
from app.core.admin_actions import AdminAction
from app.models.category import Category
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.tag import Tag
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.services.commands.audit import AuditContext, record_admin_action
from app.services.queries.posts import (
    PostConflictError,
    PostPermissionError,
    PostValidationError,
    _ensure_can_create_post,
    _ensure_can_manage_post,
    _get_post_by_slug_or_raise,
    _get_post_or_raise,
)


async def _commit_post_write(db: AsyncSession, message: str) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise PostConflictError(message) from exc


async def _get_manageable_post_or_raise(db: AsyncSession, post_id: int, *, actor: User) -> Post:
    post = await _get_post_or_raise(db, post_id, include_deleted=False)
    _ensure_can_manage_post(actor, post)
    return post


async def _ensure_user_exists(db: AsyncSession, user_id: int) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise PostValidationError(f"User with id {user_id} does not exist")


async def _ensure_category_exists(db: AsyncSession, category_id: int | None) -> None:
    if category_id is None:
        return
    category = await db.get(Category, category_id)
    if category is None:
        raise PostValidationError(f"Category with id {category_id} does not exist")


async def _ensure_slug_available(
    db: AsyncSession,
    slug: str | None,
    *,
    exclude_post_id: int | None = None,
) -> None:
    if not slug:
        return

    stmt = select(Post.id).where(Post.slug == slug)
    if exclude_post_id is not None:
        stmt = stmt.where(Post.id != exclude_post_id)
    existing_post_id = await db.scalar(stmt)
    if existing_post_id is not None:
        raise PostConflictError(f"Slug '{slug}' is already in use by post with id {existing_post_id}")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", value.lower()).strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _normalize_optional_slug(slug: str | None) -> str | None:
    if slug is None:
        return None
    normalized_slug = _slugify(slug)
    return normalized_slug or None


async def _generate_unique_slug(
    db: AsyncSession,
    title: str,
    *,
    exclude_post_id: int | None = None,
) -> str:
    base_slug = _slugify(title) or "post"
    candidate_slug = base_slug
    suffix = 2

    while True:
        stmt = select(Post.id).where(Post.slug == candidate_slug)
        if exclude_post_id is not None:
            stmt = stmt.where(Post.id != exclude_post_id)
        existing_post_id = await db.scalar(stmt)
        if existing_post_id is None:
            return candidate_slug
        candidate_slug = f"{base_slug}-{suffix}"
        suffix += 1


async def _load_tags(db: AsyncSession, tag_ids: Sequence[int]) -> list[Tag]:
    unique_ids = list(dict.fromkeys(tag_ids))
    if not unique_ids:
        return []

    stmt = select(Tag).where(Tag.id.in_(unique_ids))
    tags = await db.scalars(stmt)
    tag_by_id = {int(tag.id): tag for tag in tags}
    missing_ids = [tag_id for tag_id in unique_ids if tag_id not in tag_by_id]
    if missing_ids:
        raise PostValidationError(f"Tags with ids {missing_ids} do not exist")
    return [tag_by_id[tag_id] for tag_id in unique_ids]


async def create_post(
    db: AsyncSession,
    payload: PostCreate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
):
    _ensure_can_create_post(actor, payload.user_id)
    await _ensure_user_exists(db, payload.user_id)
    await _ensure_category_exists(db, payload.category_id)
    normalized_slug = _normalize_optional_slug(payload.slug) or await _generate_unique_slug(db, payload.title)
    await _ensure_slug_available(db, normalized_slug)
    tags = await _load_tags(db, payload.tag_ids)

    post_payload = payload.model_dump(exclude={"tag_ids"})
    post_payload["slug"] = normalized_slug
    post = Post(**post_payload)
    post.tags = tags
    db.add(post)
    await _commit_post_write(db, "Post already exists")

    created_post = await _get_post_or_raise(db, int(post.id), include_deleted=True)
    post_read_model = to_post_read_model(created_post)
    await record_admin_action(
        db,
        actor=actor,
        action=AdminAction.CREATE_POST,
        detail=f"Created post {post_read_model.id} ({post_read_model.slug})",
        audit_context=audit_context,
    )
    return post_read_model


async def update_post(
    db: AsyncSession,
    post_id: int,
    payload: PostUpdate,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
):
    post = await _get_manageable_post_or_raise(db, post_id, actor=actor)
    update_data = payload.model_dump(exclude_unset=True, exclude={"tag_ids"})

    if "slug" in update_data:
        normalized_slug = _normalize_optional_slug(update_data["slug"])
        if normalized_slug is None:
            title_for_slug = update_data.get("title", post.title)
            normalized_slug = await _generate_unique_slug(db, title_for_slug, exclude_post_id=post_id)
        await _ensure_slug_available(db, normalized_slug, exclude_post_id=post_id)
        update_data["slug"] = normalized_slug
    elif "title" in update_data and not post.slug:
        update_data["slug"] = await _generate_unique_slug(db, update_data["title"], exclude_post_id=post_id)
    if "category_id" in update_data:
        await _ensure_category_exists(db, update_data["category_id"])

    for field_name, value in update_data.items():
        setattr(post, field_name, value)

    if payload.tag_ids is not None:
        post.tags = await _load_tags(db, payload.tag_ids)

    await _commit_post_write(db, "Post update conflicts with existing data")

    updated_post = await _get_post_or_raise(db, post_id, include_deleted=False)
    post_read_model = to_post_read_model(updated_post)
    await record_admin_action(
        db,
        actor=actor,
        action=AdminAction.UPDATE_POST,
        detail=f"Updated post {post_read_model.id} ({post_read_model.slug})",
        audit_context=audit_context,
    )
    return post_read_model


async def delete_post(
    db: AsyncSession,
    post_id: int,
    *,
    actor: User,
    audit_context: AuditContext | None = None,
) -> None:
    post = await _get_manageable_post_or_raise(db, post_id, actor=actor)
    post.is_delete = 1
    await _commit_post_write(db, "Post deletion failed")
    await record_admin_action(
        db,
        actor=actor,
        action=AdminAction.DELETE_POST,
        detail=f"Deleted post {post_id} ({post.slug})",
        audit_context=audit_context,
    )


async def like_post(
    db: AsyncSession,
    slug: str,
    *,
    actor_key: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> int:
    post = await _get_post_by_slug_or_raise(db, slug, include_deleted=False)
    try:
        like = PostLike(
            post_id=int(post.id),
            actor_key=actor_key,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(like)
        await db.flush()
        await db.execute(
            update(Post)
            .where(Post.id == post.id, Post.is_delete == 0)
            .values(like_count=Post.like_count + 1)
        )
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise PostConflictError("Already liked") from exc

    like_count = await db.scalar(select(Post.like_count).where(Post.id == post.id))
    return int(like_count or 0)