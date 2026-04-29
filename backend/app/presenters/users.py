from collections.abc import Mapping

from app.models.user import User
from app.schemas.user import UserListResponse, UserOut


def present_user_out(user: User) -> UserOut:
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


def present_user_list_response(users: list[User]) -> UserListResponse:
    return UserListResponse(data=[present_user_out(user) for user in users])