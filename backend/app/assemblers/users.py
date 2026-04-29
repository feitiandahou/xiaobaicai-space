from collections.abc import Mapping

from app.core.read_models import UserReadModel
from app.models.user import User


def to_user_read_model(user: User) -> UserReadModel:
    social_links = user.social_links if isinstance(user.social_links, Mapping) else {}
    return UserReadModel(
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