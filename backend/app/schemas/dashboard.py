from datetime import datetime

from pydantic import BaseModel

from app.schemas.admin_log import AdminLogOut


class AdminDashboardOut(BaseModel):
    total_posts: int
    published_posts: int
    draft_posts: int
    category_count: int
    tag_count: int
    posts_created_last_7_days: int
    recent_logs: list[AdminLogOut]
    generated_at: datetime


class AdminDashboardResponse(BaseModel):
    data: AdminDashboardOut