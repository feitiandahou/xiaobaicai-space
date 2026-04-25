from uuid import uuid4

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status, Query, Depends
from httpx import get, post
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.post import (
    MessageResponse,
    PostCreate,
    PostUpdate,
    PostOut,
    PostListItem,
    PostResponse,
    PostListResponse,
    PostLikeResponse,
    MessageResponse,
)
from app.services.post_service import (
    PostNotFoundError,
    PostConflictError,
    PostValidationError,
    create_post as create_post_service,
    get_post as get_post_service,
    get_post_by_slug as get_post_by_slug_service,
    list_posts as list_posts_service,
    update_post as update_post_service,
    delete_post as delete_post_service,
    like_post as like_post_service,
)
from backend.app.core.database import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


def _raise_post_error(exc: Exception) -> None:
    if isinstance(exc, PostNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, PostConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, PostValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    raise exc

@router.get("", response_model=PostListResponse)
async def list_posts(
    published_only: bool = Query(False),
    include_drafts: bool = Query(False),
    status_filter: int | None = Query(None, alias="status", ge=0, le=2),
    category_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db)
) -> PostListResponse:
    posts = await list_posts_service(
        db,
        published_only=published_only,
        include_deleted=include_drafts,
        status=status_filter,
        category_id=category_id,
    )
    return PostListResponse(data=posts)

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)) -> PostResponse:
    try:
        post = await get_post_service(db, post_id)
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return PostResponse(data=post)

@router.get("/{slug}", response_model=PostResponse)
async def get_post_by_slug(slug: str, db: AsyncSession = Depends(get_db)) -> PostResponse:
    try:
        post = await get_post_by_slug_service(db, slug)
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return PostResponse(data=post)

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(payload: PostCreate, db: AsyncSession = Depends(get_db)) -> PostResponse:
    try:
        post = await create_post_service(db, payload)
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return PostResponse(data=post)

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(post_id: int, payload: PostUpdate, db: AsyncSession = Depends(get_db)) -> PostResponse:
    try:
        post = await update_post_service(db, post_id, payload)
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return PostResponse(data=post)

@router.delete("/{post_id}", response_model = MessageResponse)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    try:
        await delete_post_service(db, post_id)
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return MessageResponse(message="Post deleted successfully")

@router.post("/slug/{slug}/like", response_model=PostLikeResponse)
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
    try:
        like_count = await like_post_service(
            db,
            slug,
            actor_key=actor_key,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except (PostNotFoundError, PostConflictError, PostValidationError) as exc:
        _raise_post_error(exc)
    return PostLikeResponse(
        message="Liked successfully",
        like_count=like_count,
    )