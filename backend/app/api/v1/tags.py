from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import build_audit_context
from app.api.responses import build_error_responses
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.presenters import present_tag_list_response, present_tag_out
from app.schemas.post import MessageResponse
from app.schemas.tag import TagCreate, TagListResponse, TagResponse, TagUpdate
from app.services.commands.tags import (
    create_tag as create_tag_service,
    delete_tag as delete_tag_service,
    update_tag as update_tag_service,
)
from app.services.queries.tags import (
    get_tag as get_tag_service,
    list_manage_tags as list_manage_tags_service,
    list_public_tags as list_public_tags_service,
)


router = APIRouter(prefix="/tags", tags=["tags"])
admin_router = APIRouter(prefix="/tags", tags=["admin-tags"])


@router.get("", response_model=TagListResponse)
async def list_tags(db: AsyncSession = Depends(get_db)) -> TagListResponse:
    tags = await list_public_tags_service(db)
    return present_tag_list_response(tags)


@router.get("/{tag_id}", response_model=TagResponse, responses=build_error_responses(404, 422))
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)) -> TagResponse:
    tag = await get_tag_service(db, tag_id)
    return TagResponse(data=present_tag_out(tag))


@admin_router.get("", response_model=TagListResponse, responses=build_error_responses(401, 403))
async def list_manage_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> TagListResponse:
    tags = await list_manage_tags_service(db, actor=current_user)
    return present_tag_list_response(tags)


@admin_router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED, responses=build_error_responses(401, 403, 409, 422))
async def create_tag(
    payload: TagCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> TagResponse:
    tag = await create_tag_service(db, payload, actor=current_user, audit_context=build_audit_context(request))
    return TagResponse(data=present_tag_out(tag))


@admin_router.put("/{tag_id}", response_model=TagResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def update_tag(
    tag_id: int,
    payload: TagUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> TagResponse:
    tag = await update_tag_service(db, tag_id, payload, actor=current_user, audit_context=build_audit_context(request))
    return TagResponse(data=present_tag_out(tag))


@admin_router.delete("/{tag_id}", response_model=MessageResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def delete_tag(
    tag_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> MessageResponse:
    await delete_tag_service(db, tag_id, actor=current_user, audit_context=build_audit_context(request))
    return MessageResponse(message="Tag deleted successfully")