from uuid import uuid4

from fastapi import APIRouter, Cookie, Request, Response, status, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.audit import build_audit_context
from app.api.responses import build_error_responses
from app.presenters import present_post_list_response, present_post_out
from app.schemas.post import (
    MessageResponse,
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    PostLikeResponse,
)
from app.services.commands.posts import (
    create_post as create_post_service,
    delete_post as delete_post_service,
    like_post as like_post_service,
    update_post as update_post_service,
)
from app.services.queries.posts import (
    get_public_post as get_public_post_service,
    get_public_post_by_slug as get_public_post_by_slug_service,
    list_manage_posts as list_manage_posts_service,
    list_public_posts as list_public_posts_service,
)
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user
from app.models.user import User

router = APIRouter(prefix="/posts", tags=["posts"])
admin_router = APIRouter(prefix="/posts", tags=["admin-posts"])

@router.get("", response_model=PostListResponse, responses=build_error_responses(422))
async def list_posts(
    category_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db)
) -> PostListResponse:
    posts = await list_public_posts_service(
        db,
        category_id=category_id,
    )
    return present_post_list_response(posts)


@admin_router.get("", response_model=PostListResponse, responses=build_error_responses(401, 403, 422))
async def list_manage_posts(
    include_drafts: bool = Query(False),
    include_deleted: bool = Query(False),
    status_filter: int | None = Query(None, alias="status", ge=0, le=2),
    category_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> PostListResponse:
    posts = await list_manage_posts_service(
        db,
        include_drafts=include_drafts,
        include_deleted=include_deleted,
        status=status_filter,
        category_id=category_id,
    )
    return present_post_list_response(posts)

@router.get("/{post_id}", response_model=PostResponse, responses=build_error_responses(404, 422))
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)) -> PostResponse:
    post = await get_public_post_service(db, post_id)
    return PostResponse(data=present_post_out(post))

@router.get("/slug/{slug}", response_model=PostResponse, responses=build_error_responses(404))
async def get_post_by_slug(slug: str, db: AsyncSession = Depends(get_db)) -> PostResponse:
    post = await get_public_post_by_slug_service(db, slug)
    return PostResponse(data=present_post_out(post))

@admin_router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED, responses=build_error_responses(401, 403, 409, 422))
async def create_post(
    payload: PostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    post = await create_post_service(db, payload, actor=current_user, audit_context=build_audit_context(request))
    return PostResponse(data=present_post_out(post))

@admin_router.put("/{post_id}", response_model=PostResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def update_post(
    post_id: int,
    payload: PostUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostResponse:
    post = await update_post_service(db, post_id, payload, actor=current_user, audit_context=build_audit_context(request))
    return PostResponse(data=present_post_out(post))

@admin_router.delete("/{post_id}", response_model = MessageResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def delete_post(
    post_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    await delete_post_service(db, post_id, actor=current_user, audit_context=build_audit_context(request))
    return MessageResponse(message="Post deleted successfully")

@router.post("/slug/{slug}/like", response_model=PostLikeResponse, responses=build_error_responses(404, 409))
async def like_post(
    slug: str, 
    request: Request,
    response: Response,
    visitor_id: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> PostLikeResponse:
    actor_visitor_id = visitor_id or str(uuid4())
    actor_key = f"guest:{actor_visitor_id}"

    if visitor_id is None:
        response.set_cookie(
            key="visitor_id",
            value=actor_visitor_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 *24 * 365,  # 1 year
        )
    like_count = await like_post_service(
        db,
        slug,
        actor_key=actor_key,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return PostLikeResponse(
        message="Liked successfully",
        like_count=like_count,
    )