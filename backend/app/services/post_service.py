from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationAppError
from app.models.category import Category
from app.models.post import Post
from app.models.post_like import PostLike
from app.models.tag import Tag
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate


class PostServiceError(Exception):
    pass
class PostNotFoundError(NotFoundError, PostServiceError):
    code = ErrorCode.POST_NOT_FOUND.value
    pass
class PostConflictError(ConflictError, PostServiceError):
    code = ErrorCode.POST_CONFLICT.value
    pass
class PostValidationError(ValidationAppError, PostServiceError):
    code = ErrorCode.POST_VALIDATION_ERROR.value
    pass
class PostPermissionError(PermissionDeniedError, PostServiceError):
    code = ErrorCode.POST_PERMISSION_DENIED.value
    pass


async def _commit_post_write(db: AsyncSession, message: str) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise PostConflictError(message) from exc


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
    stmt = _post_query().where(
        Post.id == post_id,
        Post.is_delete == 0,
        Post.status == 1,
    )
    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with id {post_id} not found")
    return post


async def _get_public_post_by_slug_or_raise(db: AsyncSession, slug: str) -> Post:
    stmt = _post_query().where(
        Post.slug == slug,
        Post.is_delete == 0,
        Post.status == 1,
    )
    post = await db.scalar(stmt)
    if post is None:
        raise PostNotFoundError(f"Post with slug '{slug}' not found")
    return post


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

async def list_posts(
    db: AsyncSession,
    *,
    published_only: bool = False,
    include_drafts: bool = False,
    include_deleted: bool = False,
    status: int | None = None,
    category_id: int | None = None,
) -> list[Post]:
    stmt = _post_query().order_by(
        Post.is_top.desc(),
        Post.published_at.desc(),
        Post.created_at.desc(),
    )
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
    return list(posts)


async def list_public_posts(
    db: AsyncSession,
    *,
    category_id: int | None = None,
) -> list[Post]:
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
) -> list[Post]:
    return await list_posts(
        db,
        published_only=False,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status,
        category_id=category_id,
    )

async def get_public_post(db: AsyncSession, post_id: int) -> Post:
    return await _get_public_post_or_raise(db, post_id)

async def get_public_post_by_slug(db: AsyncSession, slug: str) -> Post:
    return await _get_public_post_by_slug_or_raise(db, slug)

async def create_post(db: AsyncSession, payload: PostCreate, *, actor: User) -> Post:
    _ensure_can_create_post(actor, payload.user_id)
    await _ensure_user_exists(db, payload.user_id)
    await _ensure_category_exists(db, payload.category_id)
    await _ensure_slug_available(db, payload.slug)
    tags = await _load_tags(db, payload.tag_ids)

    post = Post(**payload.model_dump(exclude={"tag_ids"}))
    post.tags = tags
    db.add(post)
    await _commit_post_write(db, "Post already exists")

    create_post = await _get_post_or_raise(db, int(post.id), include_deleted=True)
    return create_post

async def update_post(db: AsyncSession, post_id: int, payload: PostUpdate, *, actor: User) -> Post:
    post = await _get_manageable_post_or_raise(db, post_id, actor=actor)
    update_data = payload.model_dump(exclude_unset=True, exclude={"tag_ids"})

    if "slug" in update_data:
        await _ensure_slug_available(db, update_data["slug"], exclude_post_id=post_id)
    if "category_id" in update_data:
        await _ensure_category_exists(db, update_data["category_id"])
    
    for field_name, value in update_data.items():
        setattr(post, field_name, value)
    
    if payload.tag_ids is not None:
        post.tags = await _load_tags(db, payload.tag_ids)
    
    await _commit_post_write(db, "Post update conflicts with existing data")

    update_post = await _get_post_or_raise(db, post_id, include_deleted=False)
    return update_post

async def delete_post(db: AsyncSession, post_id: int, *, actor: User) -> None:
    post = await _get_manageable_post_or_raise(db, post_id, actor=actor)
    post.is_delete = 1
    await _commit_post_write(db, "Post deletion failed")

#No user plagiarism check and concurrency detection, abandoned
#async def like_post(db: AsyncSession, slug: str) -> int:
#	post = await _get_post_by_slug_or_raise(db, slug, include_deleted=False)
#	post.like_count = int(post.like_count) + 1
#	await db.commit()
#	return int(post.like_count)
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
    like_count = await db.scalar(
        select(Post.like_count).where(Post.id == post.id)
    )
    return int(like_count or 0)
