from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_admin, get_current_user
from app.models.user import User
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
from app.services.user_service import (
    authenticate_user as authenticate_user_service,
    change_password as change_password_service,
    create_user as create_user_service,
    get_user as get_user_service,
    list_users as list_users_service,
    update_user_status as update_user_status_service,
    update_user as update_user_service,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> UserListResponse:
    users = await list_users_service(db)
    return UserListResponse(data=users)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    user = await create_user_service(db, payload)
    return UserResponse(data=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await authenticate_user_service(db, payload.account, payload.password)

    return TokenResponse(
        access_token=create_access_token(user_id=user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await get_user_service(db, int(current_user.id), actor=current_user)
    return UserResponse(data=user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await get_user_service(db, user_id, actor=current_user)
    return UserResponse(data=user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await update_user_service(db, user_id, payload, actor=current_user)
    return UserResponse(data=user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await change_password_service(db, int(current_user.id), payload, actor=current_user)


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
) -> UserResponse:
    user = await update_user_status_service(db, user_id, payload, actor=current_user)
    return UserResponse(data=user)