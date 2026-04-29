from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import build_audit_context
from app.api.responses import build_error_responses
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_category_list_response, present_category_out
from app.schemas.category import CategoryCreate, CategoryListResponse, CategoryResponse, CategoryUpdate
from app.schemas.post import MessageResponse
from app.services.commands.categories import (
    create_category as create_category_service,
    delete_category as delete_category_service,
    update_category as update_category_service,
)
from app.services.queries.categories import (
    get_category as get_category_service,
    list_manage_categories as list_manage_categories_service,
    list_public_categories as list_public_categories_service,
)


router = APIRouter(prefix="/categories", tags=["categories"])
admin_router = APIRouter(prefix="/categories", tags=["admin-categories"])


@router.get("", response_model=CategoryListResponse)
async def list_categories(db: AsyncSession = Depends(get_db)) -> CategoryListResponse:
    categories = await list_public_categories_service(db)
    return present_category_list_response(categories)


@router.get("/{category_id}", response_model=CategoryResponse, responses=build_error_responses(404, 422))
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)) -> CategoryResponse:
    category = await get_category_service(db, category_id)
    return CategoryResponse(data=present_category_out(category))


@admin_router.get("", response_model=CategoryListResponse, responses=build_error_responses(401, 403))
async def list_manage_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> CategoryListResponse:
    categories = await list_manage_categories_service(db, actor=current_user)
    return present_category_list_response(categories)


@admin_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, responses=build_error_responses(401, 403, 409, 422))
async def create_category(
    payload: CategoryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> CategoryResponse:
    category = await create_category_service(db, payload, actor=current_user, audit_context=build_audit_context(request))
    return CategoryResponse(data=present_category_out(category))


@admin_router.put("/{category_id}", response_model=CategoryResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> CategoryResponse:
    category = await update_category_service(db, category_id, payload, actor=current_user, audit_context=build_audit_context(request))
    return CategoryResponse(data=present_category_out(category))


@admin_router.delete("/{category_id}", response_model=MessageResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def delete_category(
    category_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> MessageResponse:
    await delete_category_service(db, category_id, actor=current_user, audit_context=build_audit_context(request))
    return MessageResponse(message="Category deleted successfully")