from app.core.read_models import AdminLogReadModel
from app.models.admin_log import AdminLog


def to_admin_log_read_model(log: AdminLog) -> AdminLogReadModel:
    return AdminLogReadModel(
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