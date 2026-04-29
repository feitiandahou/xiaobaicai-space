from app.core.read_models import PostReadModel
from app.schemas.post import PostListItem, PostListResponse, PostOut


def present_post_out(post: PostReadModel) -> PostOut:
    return PostOut(
        id=int(post.id),
        user_id=int(post.user_id),
        title=post.title,
        slug=post.slug,
        summary=post.summary,
        content=post.content,
        cover_image=post.cover_image,
        category_id=int(post.category_id) if post.category_id is not None else None,
        status=int(post.status),
        is_top=int(post.is_top),
        published_at=post.published_at,
        is_delete=int(post.is_delete),
        view_count=int(post.view_count),
        like_count=int(post.like_count),
        created_at=post.created_at,
        updated_at=post.updated_at,
        tag_ids=list(post.tag_ids),
        tags=list(post.tags),
    )


def present_post_list_item(post: PostReadModel) -> PostListItem:
    return PostListItem(
        id=int(post.id),
        title=post.title,
        slug=post.slug,
        summary=post.summary,
        cover_image=post.cover_image,
        status=int(post.status),
        is_top=int(post.is_top),
        view_count=int(post.view_count),
        like_count=int(post.like_count),
        published_at=post.published_at,
        created_at=post.created_at,
        tag_ids=list(post.tag_ids),
        tags=list(post.tags),
    )


def present_post_list_response(posts: list[PostReadModel]) -> PostListResponse:
    return PostListResponse(data=[present_post_list_item(post) for post in posts])