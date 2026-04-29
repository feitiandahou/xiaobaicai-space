from app.core.read_models import AdminLogReadModel
from app.schemas.admin_log import AdminLogListResponse, AdminLogOut


def present_admin_log_out(log: AdminLogReadModel) -> AdminLogOut:
    return AdminLogOut(
        id=int(log.id),
        admin_id=int(log.admin_id),
        admin_name=log.admin_name,
        action=log.action,
        detail=log.detail,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        os_info=log.os_info,
        created_at=log.created_at,
    )


def present_admin_log_list_response(logs: list[AdminLogReadModel]) -> AdminLogListResponse:
    return AdminLogListResponse(data=[present_admin_log_out(log) for log in logs])