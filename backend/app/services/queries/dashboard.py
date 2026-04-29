from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assemblers import to_admin_log_read_model
from app.core.error_codes import ErrorCode
from app.core.errors import PermissionDeniedError
from app.core.read_models import AdminDashboardReadModel
from app.models.admin_log import AdminLog
from app.models.category import Category
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User


class DashboardQueryError(Exception):
    pass


class DashboardPermissionError(PermissionDeniedError, DashboardQueryError):
    code = ErrorCode.ADMIN_ACCESS_REQUIRED.value


def ensure_admin_access(actor: User) -> None:
    if actor.role != "admin":
        raise DashboardPermissionError("Admin access required", code=ErrorCode.ADMIN_ACCESS_REQUIRED.value)


async def get_admin_dashboard(
    db: AsyncSession,
    *,
    actor: User,
    recent_log_limit: int = 5,
) -> AdminDashboardReadModel:
    ensure_admin_access(actor)
    now = datetime.now().replace(microsecond=0)
    last_7_days = now - timedelta(days=7)

    total_posts = int(
        await db.scalar(
            select(func.count()).select_from(Post).where(Post.is_delete == 0)
        )
        or 0
    )
    published_posts = int(
        await db.scalar(
            select(func.count()).select_from(Post).where(Post.is_delete == 0, Post.status == 1)
        )
        or 0
    )
    draft_posts = int(
        await db.scalar(
            select(func.count()).select_from(Post).where(Post.is_delete == 0, Post.status == 0)
        )
        or 0
    )
    category_count = int(await db.scalar(select(func.count()).select_from(Category)) or 0)
    tag_count = int(await db.scalar(select(func.count()).select_from(Tag)) or 0)
    posts_created_last_7_days = int(
        await db.scalar(
            select(func.count()).select_from(Post).where(Post.is_delete == 0, Post.created_at >= last_7_days)
        )
        or 0
    )
    recent_logs = await db.scalars(
        select(AdminLog)
        .order_by(AdminLog.created_at.desc(), AdminLog.id.desc())
        .limit(recent_log_limit)
    )

    return AdminDashboardReadModel(
        total_posts=total_posts,
        published_posts=published_posts,
        draft_posts=draft_posts,
        category_count=category_count,
        tag_count=tag_count,
        posts_created_last_7_days=posts_created_last_7_days,
        recent_logs=[to_admin_log_read_model(log) for log in recent_logs],
        generated_at=now,
    )