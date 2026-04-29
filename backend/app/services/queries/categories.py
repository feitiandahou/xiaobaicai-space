from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_category_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationAppError
from app.core.read_models import CategoryReadModel
from app.models.category import Category
from app.models.post import Post
from app.models.user import User


class CategoryQueryError(Exception):
    pass


class CategoryNotFoundError(NotFoundError, CategoryQueryError):
    code = ErrorCode.CATEGORY_NOT_FOUND.value


class CategoryConflictError(ConflictError, CategoryQueryError):
    code = ErrorCode.CATEGORY_CONFLICT.value


class CategoryPermissionError(PermissionDeniedError, CategoryQueryError):
    code = ErrorCode.CATEGORY_PERMISSION_DENIED.value


class CategoryValidationError(ValidationAppError, CategoryQueryError):
    code = ErrorCode.CATEGORY_VALIDATION_ERROR.value


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise CategoryPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_category_record_or_raise(db: AsyncSession, category_id: int) -> Category:
    category = await db.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError(f"Category with id {category_id} not found")
    return category


async def build_category_read_model(
    db: AsyncSession,
    category: Category,
    *,
    published_only: bool,
) -> CategoryReadModel:
    stmt = select(func.count(Post.id)).where(Post.category_id == category.id, Post.is_delete == 0)
    if published_only:
        stmt = stmt.where(Post.status == 1)
    post_count = await db.scalar(stmt)
    return to_category_read_model(category, post_count=int(post_count or 0))


async def _load_categories_with_post_counts(
    db: AsyncSession,
    *,
    only_active_categories: bool,
    published_only: bool,
) -> list[CategoryReadModel]:
    join_condition = Post.category_id == Category.id
    if published_only:
        join_condition = join_condition & (Post.status == 1) & (Post.is_delete == 0)
    else:
        join_condition = join_condition & (Post.is_delete == 0)

    stmt = (
        select(Category, func.count(Post.id).label("post_count"))
        .outerjoin(Post, join_condition)
        .group_by(Category.id)
        .order_by(Category.sort_order.asc(), Category.id.asc())
    )
    if only_active_categories:
        stmt = stmt.where(Category.status == 1)

    result = await db.execute(stmt)
    return [
        to_category_read_model(category, post_count=int(post_count or 0))
        for category, post_count in result.all()
    ]


async def list_public_categories(db: AsyncSession) -> list[CategoryReadModel]:
    return await _load_categories_with_post_counts(db, only_active_categories=True, published_only=True)


async def list_manage_categories(db: AsyncSession, *, actor: User) -> list[CategoryReadModel]:
    ensure_admin_access(actor)
    return await _load_categories_with_post_counts(db, only_active_categories=False, published_only=False)


async def get_category(db: AsyncSession, category_id: int) -> CategoryReadModel:
    category = await get_category_record_or_raise(db, category_id)
    if int(category.status) != 1:
        raise CategoryNotFoundError(f"Category with id {category_id} not found")
    return await build_category_read_model(db, category, published_only=True)