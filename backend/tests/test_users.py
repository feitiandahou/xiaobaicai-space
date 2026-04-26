import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import users as users_api
from app.core.database import get_db
from app.core.security import create_access_token, get_current_admin, get_current_user
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserCreate, UserOut, UserStatusUpdate, UserUpdate
from app.services.user_service import (
    UserAuthenticationError,
    UserConflictError,
    UserInactiveError,
    UserPermissionError,
    authenticate_user,
    change_password,
    create_user,
    update_user,
    update_user_status,
)


async def _override_db():
    yield object()


@pytest.fixture
def user_app() -> FastAPI:
    app = FastAPI()
    app.include_router(users_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def _user_payload(user_id: int = 1, *, role: str = "user", is_active: bool = True) -> dict:
    now = datetime(2024, 1, 1).isoformat()
    return {
        "id": user_id,
        "username": f"user-{user_id}",
        "email": f"user{user_id}@example.com",
        "avatar": None,
        "bio": None,
        "role": role,
        "is_active": is_active,
        "social_links": {},
        "created_at": now,
        "updated_at": now,
    }


def test_list_users_requires_admin(user_app: FastAPI) -> None:
    async def deny_admin():
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    user_app.dependency_overrides[get_current_admin] = deny_admin

    with TestClient(user_app) as client:
        response = client.get("/api/v1/users")

    assert response.status_code == 403


def test_login_returns_bearer_token(user_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    auth_mock = AsyncMock(return_value=UserOut.model_validate(_user_payload(7)))
    monkeypatch.setattr(users_api, "authenticate_user_service", auth_mock)

    with TestClient(user_app) as client:
        response = client.post(
            "/api/v1/users/login",
            json={"account": "alice", "password": "secret123"},
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]
    assert response.json()["user"]["id"] == 7


def test_user_route_uses_global_exception_handler(user_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_conflict(*args, **kwargs):
        raise UserConflictError("duplicate user")

    monkeypatch.setattr(users_api, "create_user_service", raise_conflict)

    from app.core.exception_handlers import register_exception_handlers

    register_exception_handlers(user_app)

    with TestClient(user_app) as client:
        response = client.post(
            "/api/v1/users",
            json={
                "username": "alice",
                "password": "secret123",
                "email": "alice@example.com",
                "avatar": None,
                "bio": None,
                "social_links": {},
            },
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "duplicate user"}


def test_get_me_returns_current_user(user_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    user_app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=7, role="user", is_active=1)
    get_user_mock = AsyncMock(return_value=_user_payload(7))
    monkeypatch.setattr(users_api, "get_user_service", get_user_mock)

    with TestClient(user_app) as client:
        response = client.get("/api/v1/users/me")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == 7


def test_create_user_hashes_password(monkeypatch: pytest.MonkeyPatch) -> None:
    added_users: list[SimpleNamespace] = []
    created_user = SimpleNamespace(
        id=1,
        username="alice",
        password="hashed-secret",
        email="alice@example.com",
        avatar=None,
        bio=None,
        role="user",
        is_active=1,
        social_links={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )

    class FakeDB:
        def add(self, user):
            user.id = 1
            user.created_at = created_user.created_at
            user.updated_at = created_user.updated_at
            added_users.append(user)

        async def commit(self):
            return None

        async def rollback(self):
            return None

        async def scalar(self, stmt):
            return None

        async def get(self, model, user_id):
            return added_users[0]

    monkeypatch.setattr("app.services.user_service.get_password_hash", lambda raw: f"hashed-{raw}")

    result = asyncio.run(
        create_user(
            cast(AsyncSession, FakeDB()),
            UserCreate(
                username="alice",
                password="secret123",
                email="alice@example.com",
                avatar=None,
                bio=None,
                social_links={},
            ),
        )
    )

    assert added_users[0].password == "hashed-secret123"
    assert added_users[0].role == "user"
    assert result.role == "user"
    assert result.is_active is True


def test_update_user_rejects_non_admin_role_change() -> None:
    actor = cast(User, SimpleNamespace(id=2, role="user", is_active=1))
    existing_user = SimpleNamespace(
        id=2,
        username="alice",
        password="hashed",
        email="alice@example.com",
        avatar=None,
        bio=None,
        role="user",
        is_active=1,
        social_links={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )

    class FakeDB:
        async def get(self, model, user_id):
            return existing_user

        async def scalar(self, stmt):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    with pytest.raises(UserPermissionError):
        asyncio.run(update_user(cast(AsyncSession, FakeDB()), 2, UserUpdate(role="admin"), actor=actor))


def test_authenticate_user_rejects_disabled_account(monkeypatch: pytest.MonkeyPatch) -> None:
    disabled_user = SimpleNamespace(
        id=3,
        username="disabled",
        email="disabled@example.com",
        password="hashed-secret",
        role="user",
        is_active=0,
        avatar=None,
        bio=None,
        social_links={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )

    class FakeDB:
        async def scalar(self, stmt):
            return disabled_user

    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: True)

    with pytest.raises(UserInactiveError):
        asyncio.run(authenticate_user(cast(AsyncSession, FakeDB()), "disabled", "secret123"))


def test_change_password_requires_current_password(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=2, role="user", is_active=1))
    existing_user = SimpleNamespace(
        id=2,
        username="alice",
        password="hashed-current",
        email="alice@example.com",
        avatar=None,
        bio=None,
        role="user",
        is_active=1,
        social_links={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )

    class FakeDB:
        async def get(self, model, user_id):
            return existing_user

        async def commit(self):
            return None

        async def rollback(self):
            return None

    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: plain == "current123")
    monkeypatch.setattr("app.services.user_service.get_password_hash", lambda raw: f"hashed-{raw}")

    asyncio.run(
        change_password(
            cast(AsyncSession, FakeDB()),
            2,
            ChangePasswordRequest(current_password="current123", new_password="new456789"),
            actor=actor,
        )
    )
    assert existing_user.password == "hashed-new456789"

    with pytest.raises(UserAuthenticationError):
        asyncio.run(
            change_password(
                cast(AsyncSession, FakeDB()),
                2,
                ChangePasswordRequest(current_password="wrong123", new_password="another456"),
                actor=actor,
            )
        )


def test_admin_can_disable_user() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    managed_user = SimpleNamespace(
        id=2,
        username="bob",
        password="hashed",
        email="bob@example.com",
        avatar=None,
        bio=None,
        role="user",
        is_active=1,
        social_links={},
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )

    class FakeDB:
        async def get(self, model, user_id):
            return managed_user

        async def commit(self):
            return None

        async def rollback(self):
            return None

    result = asyncio.run(
        update_user_status(
            cast(AsyncSession, FakeDB()),
            2,
            UserStatusUpdate(is_active=False),
            actor=actor,
        )
    )

    assert managed_user.is_active == 0
    assert result.is_active is False


def test_create_access_token_supports_bearer_auth() -> None:
    token = create_access_token(user_id=9, expires_delta=timedelta(minutes=5))
    assert isinstance(token, str)
    assert token