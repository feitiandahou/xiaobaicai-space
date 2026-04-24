from collections.abc import Sequence
from math import e
from turtle import update

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.category import Category
from backend.app.models.post import Post
from backend.app.models.tag import Tag
from backend.app.models.user import User
from backend.app.schemas.post import PostOut, PostListItem


class PostServiceError(Exception):
    pass
class PostNotFoundError(PostServiceError):
    pass
class PostConflictError(PostServiceError):
    pass
class PostValidationError(PostServiceError):
    pass

def _post_query():
    return select(Post).options(selectinload(Post.tags))

def _serialize_post(post: Post) -> PostOut:
    tag_ids = [int(tag.id) for tag in post.tags]
    tags = [tag.name for tag in post.tags]
    return PostOut(
        id = int(post.id),
        user_id=int(post.user_id),
        title=post.title,
        slug=post.slug,
        summary=post.summary,
        content=post.content,
        cover_image=post.cover_image,
        category_id=int(post.category_id) if post.category_id is not None else None,
        status=int(post.status),
        is_top=int(post.is_top),
        published_at=post.published_at,
        is_delete=int(post.is_delete),
        view_count=int(post.view_count),
        like_count=int(post.like_count),
        created_at=post.created_at,
        updated_at=post.updated_at,
        tag_ids=tag_ids,
        tags=tags
    )
def _serialize_post_list_item(post: Post) -> PostListItem:
    tag_ids = [int(tag.id) for tag in post.tags]
    tags = [tag.name for tag in post.tags]
    return PostListItem(
        id=int(post.id),
        title=post.title,
        slug=post.slug,
        summary=post.summary,
        cover_image=post.cover_image,
        status=int(post.status),
        is_top=int(post.is_top),
        view_count=int(post.view_count),
        like_count=int(post.like_count),
        published_at=post.published_at,
        created_at=post.created_at,
        tag_ids=tag_ids,
        tags=tags,
    )

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
    include_deleted: bool = False,
    status: int | None = None,
    category_id: int | None = None,
) -> list[PostListItem]:
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
    if category_id is not None:
        stmt = stmt.where(Post.category_id == category_id)
    posts = await db.scalars(stmt)
    return [_serialize_post_list_item(post) for post in posts]