import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import posts as posts_api
from app.api.v1.admin import router as admin_api_router
from app.core.exception_handlers import register_exception_handlers
from app.core.error_codes import ErrorCode
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate
from app.services.commands.audit import AuditContext
from app.services.commands.posts import (
    create_post,
    delete_post,
    update_post,
)
from app.services.queries.posts import (
    PostConflictError,
    PostNotFoundError,
    PostPermissionError,
    get_public_post,
    list_manage_posts,
    list_public_posts,
)


async def _override_db():
    yield object()


def _post_payload(post_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=post_id,
        user_id=1,
        title="hello",
        slug="hello-world",
        summary=None,
        content="body",
        cover_image=None,
        category_id=None,
        status=1,
        is_top=0,
        published_at=None,
        is_delete=0,
        view_count=0,
        like_count=0,
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        tag_ids=[],
        tags=[],
    )


def _integrity_error() -> IntegrityError:
    return IntegrityError("statement", {}, Exception("boom"))


@pytest.fixture
def post_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(posts_api.router, prefix="/api/v1")
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_public_list_posts_enforces_published_only(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    list_posts_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(posts_api, "list_public_posts_service", list_posts_mock)

    with TestClient(post_app) as client:
        response = client.get(
            "/api/v1/posts",
            params={"include_drafts": "true", "include_deleted": "true", "status": "0", "category_id": "3"},
        )

    assert response.status_code == 200
    list_posts_mock.assert_awaited_once()
    assert list_posts_mock.await_args is not None
    _, kwargs = list_posts_mock.await_args
    assert kwargs == {"category_id": 3}


def test_post_list_validation_uses_unified_error_shape(post_app: FastAPI) -> None:
    with TestClient(post_app) as client:
        response = client.get("/api/v1/posts", params={"category_id": "0"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["detail"] == "Validation failed"
    assert response.json()["errors"][0]["loc"] == ["query", "category_id"]
    assert response.json()["errors"][0]["type"]


def test_manage_list_posts_passes_include_flags(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    list_posts_mock = AsyncMock(return_value=[])
    app_admin = cast(User, SimpleNamespace(id=1, role="admin", is_active=True))

    async def override_current_admin() -> User:
        return app_admin

    post_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(posts_api, "list_manage_posts_service", list_posts_mock)

    with TestClient(post_app) as client:
        response = client.get(
            "/api/v1/admin/posts",
            params={"include_drafts": "true", "include_deleted": "true", "status": "0", "category_id": "3"},
        )

    assert response.status_code == 200
    list_posts_mock.assert_awaited_once()
    assert list_posts_mock.await_args is not None
    _, kwargs = list_posts_mock.await_args
    assert kwargs["include_drafts"] is True
    assert kwargs["include_deleted"] is True
    assert kwargs["status"] == 0
    assert kwargs["category_id"] == 3


def test_manage_list_posts_requires_admin(post_app: FastAPI) -> None:
    with TestClient(post_app) as client:
        response = client.get("/api/v1/admin/posts")

    assert response.status_code == 401
    assert response.json() == {"code": ErrorCode.AUTHENTICATION_REQUIRED.value, "detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_posts_openapi_declares_unified_error_models(post_app: FastAPI) -> None:
    schema = post_app.openapi()
    get_post_operation = schema["paths"]["/api/v1/posts/{post_id}"]["get"]

    assert get_post_operation["responses"]["404"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
    assert get_post_operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ValidationErrorResponse"
    assert get_post_operation["responses"]["404"]["description"] == "Resource not found"
    assert get_post_operation["responses"]["404"]["content"]["application/json"]["example"] == {
        "code": ErrorCode.NOT_FOUND.value,
        "detail": "Resource not found",
    }


def test_list_public_posts_applies_published_only_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    list_posts_mock = AsyncMock(return_value=[])
    db = cast(AsyncSession, SimpleNamespace())
    monkeypatch.setattr("app.services.queries.posts.list_posts", list_posts_mock)

    result = asyncio.run(list_public_posts(db, category_id=7))

    assert result == []
    list_posts_mock.assert_awaited_once_with(
        db,
        published_only=True,
        include_drafts=False,
        include_deleted=False,
        status=None,
        category_id=7,
    )


def test_list_manage_posts_passes_management_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    list_posts_mock = AsyncMock(return_value=[])
    db = cast(AsyncSession, SimpleNamespace())
    monkeypatch.setattr("app.services.queries.posts.list_posts", list_posts_mock)

    result = asyncio.run(
        list_manage_posts(
            db,
            include_drafts=True,
            include_deleted=True,
            status=2,
            category_id=5,
        )
    )

    assert result == []
    list_posts_mock.assert_awaited_once_with(
        db,
        published_only=False,
        include_drafts=True,
        include_deleted=True,
        status=2,
        category_id=5,
    )


def test_slug_route_is_namespaced(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    get_by_slug_mock = AsyncMock(return_value=_post_payload())
    get_by_id_mock = AsyncMock()
    monkeypatch.setattr(posts_api, "get_public_post_by_slug_service", get_by_slug_mock)
    monkeypatch.setattr(posts_api, "get_public_post_service", get_by_id_mock)

    with TestClient(post_app) as client:
        response = client.get("/api/v1/posts/slug/hello-world")

    assert response.status_code == 200
    get_by_slug_mock.assert_awaited_once()
    get_by_id_mock.assert_not_called()


def test_public_post_route_uses_public_read_service(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    get_public_post_mock = AsyncMock(return_value=_post_payload())
    monkeypatch.setattr(posts_api, "get_public_post_service", get_public_post_mock)

    with TestClient(post_app) as client:
        response = client.get("/api/v1/posts/1")

    assert response.status_code == 200
    get_public_post_mock.assert_awaited_once()


def test_get_public_post_filters_to_published_and_not_deleted() -> None:
    captured_stmt = None

    class CapturingDb:
        async def scalar(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return None

    with pytest.raises(PostNotFoundError):
        asyncio.run(get_public_post(cast(AsyncSession, CapturingDb()), 1))

    assert captured_stmt is not None
    compiled = str(captured_stmt)
    assert "posts.id = :id_1" in compiled
    assert "posts.is_delete = :is_delete_1" in compiled
    assert "posts.status = :status_1" in compiled


def test_post_route_uses_global_exception_handler(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_not_found(*args, **kwargs):
        raise PostNotFoundError("missing post")

    monkeypatch.setattr(posts_api, "get_public_post_service", raise_not_found)

    from app.core.exception_handlers import register_exception_handlers

    register_exception_handlers(post_app)

    with TestClient(post_app) as client:
        response = client.get("/api/v1/posts/1")

    assert response.status_code == 404
    assert response.json() == {"code": ErrorCode.POST_NOT_FOUND.value, "detail": "missing post"}


def test_create_post_rejects_other_author() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="user"))
    payload = PostCreate(title="title", content="body", user_id=2, tag_ids=[])

    with pytest.raises(PostPermissionError):
        asyncio.run(create_post(cast(AsyncSession, SimpleNamespace()), payload, actor=actor))


def test_update_post_rejects_non_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="user"))
    db = cast(AsyncSession, SimpleNamespace(commit=AsyncMock()))

    async def fake_get_post_or_raise(*args, **kwargs):
        return SimpleNamespace(user_id=2, tags=[])

    monkeypatch.setattr("app.services.commands.posts._get_post_or_raise", fake_get_post_or_raise)

    with pytest.raises(PostPermissionError):
        asyncio.run(update_post(db, 10, PostUpdate(title="changed"), actor=actor))


def test_create_post_rolls_back_and_translates_integrity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="user"))
    rollback_mock = AsyncMock()
    db = cast(
        AsyncSession,
        SimpleNamespace(add=lambda *_args, **_kwargs: None, commit=AsyncMock(side_effect=_integrity_error()), rollback=rollback_mock),
    )

    async def noop(*args, **kwargs):
        return None

    async def fake_load_tags(*args, **kwargs):
        return []

    monkeypatch.setattr("app.services.commands.posts._ensure_user_exists", noop)
    monkeypatch.setattr("app.services.commands.posts._ensure_category_exists", noop)
    monkeypatch.setattr("app.services.commands.posts._ensure_slug_available", noop)
    monkeypatch.setattr("app.services.commands.posts._load_tags", fake_load_tags)

    payload = PostCreate(title="title", content="body", user_id=1, tag_ids=[])

    with pytest.raises(PostConflictError, match="Post already exists"):
        asyncio.run(create_post(db, payload, actor=actor))

    rollback_mock.assert_awaited_once()


def test_create_post_records_admin_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", username="admin"))
    audit_mock = AsyncMock()
    created_post = _post_payload(22)

    class FakeDb:
        def add(self, post):
            post.id = 22
            post.tags = []

        async def commit(self):
            return None

        async def rollback(self):
            return None

    async def noop(*args, **kwargs):
        return None

    async def fake_load_tags(*args, **kwargs):
        return []

    async def fake_get_post_or_raise(*args, **kwargs):
        return created_post

    monkeypatch.setattr("app.services.commands.posts._ensure_user_exists", noop)
    monkeypatch.setattr("app.services.commands.posts._ensure_category_exists", noop)
    monkeypatch.setattr("app.services.commands.posts._ensure_slug_available", noop)
    monkeypatch.setattr("app.services.commands.posts._load_tags", fake_load_tags)
    monkeypatch.setattr("app.services.commands.posts._get_post_or_raise", fake_get_post_or_raise)
    monkeypatch.setattr("app.services.commands.posts.record_admin_action", audit_mock)

    result = asyncio.run(
        create_post(
            cast(AsyncSession, FakeDb()),
            PostCreate(title="title", content="body", user_id=1, tag_ids=[]),
            actor=actor,
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert result.id == 22
    audit_mock.assert_awaited_once()


def test_update_post_rolls_back_and_translates_integrity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="user"))
    rollback_mock = AsyncMock()
    db = cast(AsyncSession, SimpleNamespace(commit=AsyncMock(side_effect=_integrity_error()), rollback=rollback_mock))

    async def fake_get_post_or_raise(*args, **kwargs):
        return SimpleNamespace(id=10, user_id=1, tags=[], title="old")

    monkeypatch.setattr("app.services.commands.posts._get_post_or_raise", fake_get_post_or_raise)

    with pytest.raises(PostConflictError, match="Post update conflicts with existing data"):
        asyncio.run(update_post(db, 10, PostUpdate(title="changed"), actor=actor))

    rollback_mock.assert_awaited_once()


def test_delete_post_rolls_back_and_translates_integrity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="user"))
    rollback_mock = AsyncMock()
    db = cast(AsyncSession, SimpleNamespace(commit=AsyncMock(side_effect=_integrity_error()), rollback=rollback_mock))
    post = SimpleNamespace(id=10, user_id=1, is_delete=0)

    async def fake_get_post_or_raise(*args, **kwargs):
        return post

    monkeypatch.setattr("app.services.commands.posts._get_post_or_raise", fake_get_post_or_raise)

    with pytest.raises(PostConflictError, match="Post deletion failed"):
        asyncio.run(delete_post(db, 10, actor=actor))

    assert post.is_delete == 1
    rollback_mock.assert_awaited_once()