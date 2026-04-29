from app.core.read_models import TagReadModel
from app.models.tag import Tag


def to_tag_read_model(tag: Tag, *, post_count: int) -> TagReadModel:
    return TagReadModel(
        id=int(tag.id),
        name=tag.name,
        slug=tag.slug,
        post_count=int(post_count),
        created_at=tag.created_at,
    )