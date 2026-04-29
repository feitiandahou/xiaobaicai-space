from app.core.read_models import TagReadModel
from app.schemas.tag import TagListResponse, TagOut


def present_tag_out(tag: TagReadModel) -> TagOut:
    return TagOut(
        id=int(tag.id),
        name=tag.name,
        slug=tag.slug,
        post_count=int(getattr(tag, "post_count", 0)),
        created_at=tag.created_at,
    )


def present_tag_list_response(tags: list[TagReadModel]) -> TagListResponse:
    return TagListResponse(data=[present_tag_out(tag) for tag in tags])