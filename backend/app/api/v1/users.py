from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.audit import build_audit_context
from app.api.responses import build_error_responses
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_admin, get_current_user
from app.models.user import User
from app.presenters import present_user_list_response, present_user_out
from app.schemas.user import (
    ChangePasswordRequest,
    TokenResponse,
    UserCreate,
    UserListResponse,
    UserLogin,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.commands.users import (
    change_password as change_password_service,
    create_user as create_user_service,
    update_user_status as update_user_status_service,
    update_user as update_user_service,
)
from app.services.queries.users import (
    authenticate_user as authenticate_user_service,
    get_user as get_user_service,
    list_users as list_users_service,
)

router = APIRouter(prefix="/users", tags=["users"])
admin_router = APIRouter(prefix="/users", tags=["admin-users"])


@admin_router.get("", response_model=UserListResponse, responses=build_error_responses(401, 403))
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> UserListResponse:
    users = await list_users_service(db)
    return present_user_list_response(users)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED, responses=build_error_responses(409, 422))
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await create_user_service(db, payload)
    return UserResponse(data=present_user_out(user))


@router.post("/login", response_model=TokenResponse, responses=build_error_responses(401, 403, 422))
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await authenticate_user_service(db, payload.account, payload.password)

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=present_user_out(user),
    )


@router.get("/me", response_model=UserResponse, responses=build_error_responses(401, 403))
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await get_user_service(db, int(current_user.id), actor=current_user)
    return UserResponse(data=present_user_out(user))


@router.get("/{user_id}", response_model=UserResponse, responses=build_error_responses(401, 403, 404, 422))
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await get_user_service(db, user_id, actor=current_user)
    return UserResponse(data=present_user_out(user))


@router.put("/{user_id}", response_model=UserResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await update_user_service(db, user_id, payload, actor=current_user, audit_context=build_audit_context(request))
    return UserResponse(data=present_user_out(user))


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT, responses=build_error_responses(401, 403, 404, 409, 422))
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await change_password_service(db, int(current_user.id), payload, actor=current_user, audit_context=build_audit_context(request))


@admin_router.patch("/{user_id}/status", response_model=UserResponse, responses=build_error_responses(401, 403, 404, 409, 422))
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> UserResponse:
    user = await update_user_status_service(db, user_id, payload, actor=current_user, audit_context=build_audit_context(request))
    return UserResponse(data=present_user_out(user))