from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.assemblers import to_post_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationAppError
from app.core.read_models import PostReadModel
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
) -> list[PostReadModel]:
    stmt = _post_query().order_by(Post.is_top.desc(), Post.published_at.desc(), Post.created_at.desc())
    if not include_deleted:
        stmt = stmt.where(Post.is_delete == 0)
    if published_only:
        stmt = stmt.where(Post.status == 1)
    elif status is not None:
        stmt = stmt.where(Post.status == status)
    elif not include_drafts:
        stmt = stmt.where(Post.status != 0)
    if category_id is not None:
        stmt = stmt.where(Post.category_id == category_id)
    posts = await db.scalars(stmt)
    return [to_post_read_model(post) for post in posts]


async def list_public_posts(db: AsyncSession, *, category_id: int | None = None) -> list[PostReadModel]:
    return await list_posts(
        db,
        published_only=True,
        include_drafts=False,
        include_deleted=False,
        status=None,
        category_id=category_id,
    )


async def list_manage_posts(
    db: AsyncSession,
    *,
    include_drafts: bool = False,
    include_deleted: bool = False,
    status: int | None = None,
    category_id: int | None = None,
) -> list[PostReadModel]:
    return await list_posts(
        db,
        published_only=False,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status,
        category_id=category_id,
    )


async def get_public_post(db: AsyncSession, post_id: int) -> PostReadModel:
    post = await _get_public_post_or_raise(db, post_id)
    return to_post_read_model(post)


async def get_public_post_by_slug(db: AsyncSession, slug: str) -> PostReadModel:
    post = await _get_public_post_by_slug_or_raise(db, slug)
    return to_post_read_model(post)