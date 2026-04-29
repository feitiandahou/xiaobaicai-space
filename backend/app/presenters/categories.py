from app.core.read_models import CategoryReadModel
from app.schemas.category import CategoryListResponse, CategoryOut


def present_category_out(category: CategoryReadModel) -> CategoryOut:
    return CategoryOut(
        id=int(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        parent_id=int(category.parent_id),
        sort_order=int(category.sort_order),
        icon=category.icon,
        status=int(category.status),
        post_count=int(getattr(category, "post_count", 0)),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def present_category_list_response(categories: list[CategoryReadModel]) -> CategoryListResponse:
    return CategoryListResponse(data=[present_category_out(category) for category in categories])