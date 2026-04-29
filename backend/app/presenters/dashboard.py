from app.core.read_models import AdminDashboardReadModel
from app.presenters.admin_logs import present_admin_log_out
from app.schemas.dashboard import AdminDashboardOut, AdminDashboardResponse


def present_admin_dashboard_out(dashboard: AdminDashboardReadModel) -> AdminDashboardOut:
    return AdminDashboardOut(
        total_posts=dashboard.total_posts,
        published_posts=dashboard.published_posts,
        draft_posts=dashboard.draft_posts,
        category_count=dashboard.category_count,
        tag_count=dashboard.tag_count,
        posts_created_last_7_days=dashboard.posts_created_last_7_days,
        recent_logs=[present_admin_log_out(log) for log in dashboard.recent_logs],
        generated_at=dashboard.generated_at,
    )


def present_admin_dashboard_response(dashboard: AdminDashboardReadModel) -> AdminDashboardResponse:
    return AdminDashboardResponse(data=present_admin_dashboard_out(dashboard))