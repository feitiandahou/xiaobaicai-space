from app.core.read_models import CategoryReadModel
from app.models.category import Category


def to_category_read_model(category: Category, *, post_count: int) -> CategoryReadModel:
    return CategoryReadModel(
        id=int(category.id),
        name=category.name,
        slug=category.slug,
        description=category.description,
        parent_id=int(category.parent_id),
        sort_order=int(category.sort_order),
        icon=category.icon,
        status=int(category.status),
        post_count=int(post_count),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )