from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_tag_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError
from app.core.read_models import TagReadModel
from app.models.post import Post, post_tags
from app.models.tag import Tag
from app.models.user import User


class TagQueryError(Exception):
    pass


class TagNotFoundError(NotFoundError, TagQueryError):
    code = ErrorCode.TAG_NOT_FOUND.value


class TagConflictError(ConflictError, TagQueryError):
    code = ErrorCode.TAG_CONFLICT.value


class TagPermissionError(PermissionDeniedError, TagQueryError):
    code = ErrorCode.TAG_PERMISSION_DENIED.value


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise TagPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_tag_record_or_raise(db: AsyncSession, tag_id: int) -> Tag:
    tag = await db.get(Tag, tag_id)
    if tag is None:
        raise TagNotFoundError(f"Tag with id {tag_id} not found")
    return tag


async def build_tag_read_model(db: AsyncSession, tag: Tag, *, published_only: bool) -> TagReadModel:
    stmt = (
        select(func.count(Post.id))
        .select_from(post_tags.join(Post, Post.id == post_tags.c.post_id))
        .where(post_tags.c.tag_id == tag.id, Post.is_delete == 0)
    )
    if published_only:
        stmt = stmt.where(Post.status == 1)
    post_count = await db.scalar(stmt)
    return to_tag_read_model(tag, post_count=int(post_count or 0))


async def _load_tags_with_post_counts(db: AsyncSession, *, published_only: bool) -> list[TagReadModel]:
    join_condition = post_tags.c.tag_id == Tag.id
    post_join_condition = Post.id == post_tags.c.post_id
    if published_only:
        post_join_condition = post_join_condition & (Post.status == 1) & (Post.is_delete == 0)
    else:
        post_join_condition = post_join_condition & (Post.is_delete == 0)

    stmt = (
        select(Tag, func.count(Post.id).label("post_count"))
        .outerjoin(post_tags, join_condition)
        .outerjoin(Post, post_join_condition)
        .group_by(Tag.id)
        .order_by(Tag.name.asc(), Tag.id.asc())
    )
    result = await db.execute(stmt)
    return [to_tag_read_model(tag, post_count=int(post_count or 0)) for tag, post_count in result.all()]


async def list_public_tags(db: AsyncSession) -> list[TagReadModel]:
    return await _load_tags_with_post_counts(db, published_only=True)


async def list_manage_tags(db: AsyncSession, *, actor: User) -> list[TagReadModel]:
    ensure_admin_access(actor)
    return await _load_tags_with_post_counts(db, published_only=False)


async def get_tag(db: AsyncSession, tag_id: int) -> TagReadModel:
    tag = await get_tag_record_or_raise(db, tag_id)
    return await build_tag_read_model(db, tag, published_only=True)