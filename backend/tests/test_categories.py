from datetime import datetime
import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import categories as categories_api
from app.api.v1.admin import router as admin_api_router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import get_current_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.commands.audit import AuditContext
from app.services.commands.categories import (
    create_category,
    update_category,
)
from app.services.queries.categories import (
    CategoryConflictError,
    CategoryNotFoundError,
    CategoryValidationError,
    list_public_categories,
)


async def _override_db():
    yield object()


def _category_payload(category_id: int = 1) -> SimpleNamespace:
    now = datetime(2024, 1, 1)
    return SimpleNamespace(
        id=category_id,
        name="Tech",
        slug="tech",
        description="Tech posts",
        parent_id=0,
        sort_order=0,
        icon=None,
        status=1,
        post_count=2,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def category_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(categories_api.router, prefix="/api/v1")
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_public_category_list_route_uses_public_service(category_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    list_categories_mock = AsyncMock(return_value=[_category_payload()])
    monkeypatch.setattr(categories_api, "list_public_categories_service", list_categories_mock)

    with TestClient(category_app) as client:
        response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert response.json()["data"][0]["slug"] == "tech"
    assert response.json()["data"][0]["post_count"] == 2


def test_manage_category_list_requires_admin(category_app: FastAPI) -> None:
    with TestClient(category_app) as client:
        response = client.get("/api/v1/admin/categories")

    assert response.status_code == 401


def test_manage_category_list_uses_admin_service(category_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_categories_mock = AsyncMock(return_value=[_category_payload()])

    async def override_current_admin() -> User:
        return admin_user

    category_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(categories_api, "list_manage_categories_service", list_categories_mock)

    with TestClient(category_app) as client:
        response = client.get("/api/v1/admin/categories")

    assert response.status_code == 200
    list_categories_mock.assert_awaited_once()


def test_public_category_route_uses_global_exception_handler(category_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_not_found(*args, **kwargs):
        raise CategoryNotFoundError("missing category", code="category_not_found")

    monkeypatch.setattr(categories_api, "get_category_service", raise_not_found)

    with TestClient(category_app) as client:
        response = client.get("/api/v1/categories/1")

    assert response.status_code == 404
    assert response.json() == {"code": "category_not_found", "detail": "missing category"}


def test_list_public_categories_filters_active_only(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_stmt = None

    class CapturingDb:
        async def execute(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return SimpleNamespace(all=lambda: [])

    result = asyncio.run(list_public_categories(cast(AsyncSession, CapturingDb())))

    assert result == []
    assert captured_stmt is not None
    compiled = str(captured_stmt)
    assert "WHERE categories.status = :status_" in compiled
    assert "posts.status = :status_" in compiled


def test_get_category_attaches_public_post_count() -> None:
    category = _category_payload()

    class FakeDb:
        async def get(self, model, category_id):
            return category

        async def scalar(self, stmt):
            return 4

    result = asyncio.run(categories_api.get_category_service(cast(AsyncSession, FakeDb()), 1))

    assert result.post_count == 4


def test_create_category_rejects_missing_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))

    class FakeDb:
        async def scalar(self, stmt):
            return None

        async def get(self, model, category_id):
            return None

    with pytest.raises(CategoryValidationError):
        pytest.importorskip("asyncio").run(
            create_category(
                cast(AsyncSession, FakeDb()),
                CategoryCreate(name="Tech", slug="tech", parent_id=99),
                actor=actor,
            )
        )


def test_update_category_rejects_self_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    category = _category_payload(10)

    class FakeDb:
        async def get(self, model, category_id):
            return category

        async def scalar(self, stmt):
            return None

    with pytest.raises(CategoryValidationError):
        pytest.importorskip("asyncio").run(
            update_category(
                cast(AsyncSession, FakeDb()),
                10,
                CategoryUpdate(parent_id=10),
                actor=actor,
            )
        )


def test_create_category_conflict_uses_specific_code(category_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))

    async def override_current_admin() -> User:
        return admin_user

    async def raise_conflict(*args, **kwargs):
        raise CategoryConflictError("duplicate category")

    category_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(categories_api, "create_category_service", raise_conflict)

    with TestClient(category_app) as client:
        response = client.post("/api/v1/admin/categories", json={"name": "Tech", "slug": "tech"})

    assert response.status_code == 409
    assert response.json() == {"code": "category_conflict", "detail": "duplicate category"}


def test_create_category_records_admin_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", username="admin"))
    audit_mock = AsyncMock()

    class FakeDb:
        def add(self, category):
            category.id = 12
            category.created_at = datetime(2024, 1, 1)
            category.updated_at = datetime(2024, 1, 1)

        async def commit(self):
            return None

        async def rollback(self):
            return None

        async def scalar(self, stmt):
            return None

        async def get(self, model, category_id):
            return _category_payload(12)

    monkeypatch.setattr("app.services.commands.categories.record_admin_action", audit_mock)

    result = asyncio.run(
        create_category(
            cast(AsyncSession, FakeDb()),
            CategoryCreate(name="Tech", slug="tech"),
            actor=actor,
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert result.id == 12
    audit_mock.assert_awaited_once()