from datetime import datetime
from math import ceil
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assemblers import to_post_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationAppError
from app.core.read_models import PostListPageReadModel, PostReadModel
from app.models.post import Post
from app.models.user import User


class PostQueryError(Exception):
    pass


class PostNotFoundError(NotFoundError, PostQueryError):
    code = ErrorCode.POST_NOT_FOUND.value


class PostConflictError(ConflictError, PostQueryError):
    code = ErrorCode.POST_CONFLICT.value


class PostValidationError(ValidationAppError, PostQueryError):
    code = ErrorCode.POST_VALIDATION_ERROR.value


class PostPermissionError(PermissionDeniedError, PostQueryError):
    code = ErrorCode.POST_PERMISSION_DENIED.value


def _is_admin(actor: User) -> bool:
    return actor.role == "admin"


def _ensure_can_create_post(actor: User, author_id: int) -> None:
    if _is_admin(actor):
        return
    if int(actor.id) != author_id:
        raise PostPermissionError("Not allowed to create posts for another user")


def _ensure_can_manage_post(actor: User, post: Post) -> None:
    if _is_admin(actor):
        return
    if int(actor.id) != int(post.user_id):
        raise PostPermissionError("Not allowed to modify this post")


def _post_query():
    return select(Post).options(selectinload(Post.tags))


def _apply_post_sorting(
    stmt,
    *,
    sort_by: Literal["created_at", "published_at", "view_count"],
    sort_order: Literal["asc", "desc"],
):
    sort_columns = {
        "created_at": Post.created_at,
        "published_at": Post.published_at,
        "view_count": Post.view_count,
    }
    sort_column = sort_columns[sort_by]
    if sort_order == "asc":
        return stmt.order_by(Post.is_top.desc(), sort_column.asc(), Post.id.asc())
    return stmt.order_by(Post.is_top.desc(), sort_column.desc(), Post.id.desc())


def _apply_post_filters(
    stmt,
    *,
    published_only: bool,
    include_drafts: bool,
    include_deleted: bool,
    status: int | None,
    category_id: int | None,
    author_id: int | None,
    search: str | None,
    created_from: datetime | None,
    created_to: datetime | None,
):
    if created_from is not None and created_to is not None and created_from > created_to:
        raise PostValidationError("created_from must be earlier than or equal to created_to")
    if not include_deleted:
        stmt = stmt.where(Post.is_delete == 0)
    if published_only:
        stmt = stmt.where(Post.status == 1, Post.slug.is_not(None))
    elif status is not None:
        stmt = stmt.where(Post.status == status)
    elif not include_drafts:
        stmt = stmt.where(Post.status != 0)
    if category_id is not None:
        stmt = stmt.where(Post.category_id == category_id)
    if author_id is not None:
        stmt = stmt.where(Post.user_id == author_id)
    if search:
        keyword = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Post.title.ilike(keyword),
                Post.slug.ilike(keyword),
                Post.summary.ilike(keyword),
            )
        )
    if created_from is not None:
        stmt = stmt.where(Post.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(Post.created_at <= created_to)
    return stmt


async def _get_post_or_raise(
    db: AsyncSession,
    post_id: int,
    *,
    include_deleted: bool = False,
) -> Post:
    stmt = _post_query().where(Post.id == post_id)
    if not include_deleted:
        stmt = stmt.where(Post.is_delete == 0)

    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with id {post_id} not found")
    return post


async def _get_post_by_slug_or_raise(
    db: AsyncSession,
    slug: str,
    *,
    include_deleted: bool = False,
) -> Post:
    stmt = _post_query().where(Post.slug == slug)
    if not include_deleted:
        stmt = stmt.where(Post.is_delete == 0)

    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with slug '{slug}' not found")
    return post


async def _get_public_post_or_raise(db: AsyncSession, post_id: int) -> Post:
    stmt = _post_query().where(Post.id == post_id, Post.is_delete == 0, Post.status == 1)
    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with id {post_id} not found")
    return post


async def _get_public_post_by_slug_or_raise(db: AsyncSession, slug: str) -> Post:
    stmt = _post_query().where(Post.slug == slug, Post.is_delete == 0, Post.status == 1)
    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with slug '{slug}' not found")
    return post


async def list_posts(
    db: AsyncSession,
    *,
    published_only: bool = False,
    include_drafts: bool = False,
    include_deleted: bool = False,
    status: int | None = None,
    category_id: int | None = None,
    author_id: int | None = None,
    search: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: Literal["created_at", "published_at", "view_count"] = "published_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    page_size: int = 10,
) -> PostListPageReadModel:
    base_stmt = _apply_post_filters(
        _post_query(),
        published_only=published_only,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status,
        category_id=category_id,
        author_id=author_id,
        search=search,
        created_from=created_from,
        created_to=created_to,
    )
    stmt = _apply_post_sorting(base_stmt, sort_by=sort_by, sort_order=sort_order).offset((page - 1) * page_size).limit(page_size)
    total_stmt = _apply_post_filters(
        select(func.count()).select_from(Post),
        published_only=published_only,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status,
        category_id=category_id,
        author_id=author_id,
        search=search,
        created_from=created_from,
        created_to=created_to,
    )
    posts = await db.scalars(stmt)
    total = int(await db.scalar(total_stmt) or 0)
    total_pages = ceil(total / page_size) if total > 0 else 0
    return PostListPageReadModel(
        data=[to_post_read_model(post) for post in posts],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1 and total_pages > 0,
    )


async def list_public_posts(
    db: AsyncSession,
    *,
    category_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PostListPageReadModel:
    return await list_posts(
        db,
        published_only=True,
        include_drafts=False,
        include_deleted=False,
        status=None,
        category_id=category_id,
        author_id=None,
        search=search,
        created_from=None,
        created_to=None,
        sort_by="published_at",
        sort_order="desc",
        page=page,
        page_size=page_size,
    )


async def list_manage_posts(
    db: AsyncSession,
    *,
    include_drafts: bool = False,
    include_deleted: bool = False,
    status: int | None = None,
    category_id: int | None = None,
    author_id: int | None = None,
    search: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: Literal["created_at", "published_at", "view_count"] = "published_at",
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = 1,
    page_size: int = 10,
) -> PostListPageReadModel:
    return await list_posts(
        db,
        published_only=False,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status,
        category_id=category_id,
        author_id=author_id,
        search=search,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


async def get_public_post(db: AsyncSession, post_id: int) -> PostReadModel:
    post = await _get_public_post_or_raise(db, post_id)
    return to_post_read_model(post)


async def get_manage_post(db: AsyncSession, post_id: int, *, actor: User) -> PostReadModel:
    post = await _get_post_or_raise(db, post_id)
    _ensure_can_manage_post(actor, post)
    return to_post_read_model(post)


async def get_public_post_by_slug(db: AsyncSession, slug: str) -> PostReadModel:
    post = await _get_public_post_by_slug_or_raise(db, slug)
    return to_post_read_model(post)