from collections.abc import Mapping

from app.core.read_models import UserListPageReadModel, UserReadModel
from app.schemas.user import UserListMeta, UserListResponse, UserOut


def present_user_out(user: UserReadModel) -> UserOut:
    social_links = user.social_links if isinstance(user.social_links, Mapping) else {}
    return UserOut(
        id=int(user.id),
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        bio=user.bio,
        role=user.role,
        is_active=bool(user.is_active),
        social_links=dict(social_links),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def present_user_list_response(users: UserListPageReadModel) -> UserListResponse:
    return UserListResponse(
        data=[present_user_out(user) for user in users.data],
        meta=UserListMeta(
            page=users.page,
            page_size=users.page_size,
            total=users.total,
            total_pages=users.total_pages,
            has_next=users.has_next,
            has_prev=users.has_prev,
        ),
    )