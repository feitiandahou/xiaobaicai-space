import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import tags as tags_api
from app.api.v1.admin import router as admin_api_router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import get_current_admin
from app.models.user import User
from app.schemas.tag import TagCreate, TagUpdate
from app.services.commands.audit import AuditContext
from app.services.commands.tags import create_tag, update_tag
from app.services.queries.tags import TagConflictError, TagNotFoundError, list_public_tags


async def _override_db():
    yield object()


def _tag_payload(tag_id: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        id=tag_id,
        name="python",
        slug="python",
        post_count=3,
        created_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def tag_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(tags_api.router, prefix="/api/v1")
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_public_tag_list_route_uses_public_service(tag_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    list_tags_mock = AsyncMock(return_value=[_tag_payload()])
    monkeypatch.setattr(tags_api, "list_public_tags_service", list_tags_mock)

    with TestClient(tag_app) as client:
        response = client.get("/api/v1/tags")

    assert response.status_code == 200
    assert response.json()["data"][0]["slug"] == "python"
    assert response.json()["data"][0]["post_count"] == 3


def test_manage_tag_list_requires_admin(tag_app: FastAPI) -> None:
    with TestClient(tag_app) as client:
        response = client.get("/api/v1/admin/tags")

    assert response.status_code == 401


def test_manage_tag_list_uses_admin_service(tag_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_tags_mock = AsyncMock(return_value=[_tag_payload()])

    async def override_current_admin() -> User:
        return admin_user

    tag_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(tags_api, "list_manage_tags_service", list_tags_mock)

    with TestClient(tag_app) as client:
        response = client.get("/api/v1/admin/tags")

    assert response.status_code == 200
    list_tags_mock.assert_awaited_once()


def test_public_tag_route_uses_global_exception_handler(tag_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    async def raise_not_found(*args, **kwargs):
        raise TagNotFoundError("missing tag")

    monkeypatch.setattr(tags_api, "get_tag_service", raise_not_found)

    with TestClient(tag_app) as client:
        response = client.get("/api/v1/tags/1")

    assert response.status_code == 404
    assert response.json() == {"code": "tag_not_found", "detail": "missing tag"}


def test_list_public_tags_orders_by_name() -> None:
    captured_stmt = None

    class CapturingDb:
        async def execute(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return SimpleNamespace(all=lambda: [])

    result = asyncio.run(list_public_tags(cast(AsyncSession, CapturingDb())))

    assert result == []
    assert captured_stmt is not None
    compiled = str(captured_stmt)
    assert "ORDER BY tags.name ASC" in compiled
    assert "posts.status = :status_" in compiled


def test_get_tag_attaches_public_post_count() -> None:
    tag = _tag_payload()

    class FakeDb:
        async def get(self, model, tag_id):
            return tag

        async def scalar(self, stmt):
            return 5

    result = asyncio.run(tags_api.get_tag_service(cast(AsyncSession, FakeDb()), 1))

    assert result.post_count == 5


def test_create_tag_enforces_unique_fields() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))

    class FakeDb:
        async def scalar(self, stmt):
            return 1

    with pytest.raises(TagConflictError):
        asyncio.run(create_tag(cast(AsyncSession, FakeDb()), TagCreate(name="python", slug="python"), actor=actor))


def test_update_tag_conflict_uses_specific_code(tag_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))

    async def override_current_admin() -> User:
        return admin_user

    async def raise_conflict(*args, **kwargs):
        raise TagConflictError("duplicate tag")

    tag_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(tags_api, "update_tag_service", raise_conflict)

    with TestClient(tag_app) as client:
        response = client.put("/api/v1/admin/tags/1", json={"slug": "python"})

    assert response.status_code == 409
    assert response.json() == {"code": "tag_conflict", "detail": "duplicate tag"}


def test_update_tag_updates_raw_model() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    tag = _tag_payload(10)

    class FakeDb:
        async def get(self, model, tag_id):
            return tag

        async def scalar(self, stmt):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    result = asyncio.run(update_tag(cast(AsyncSession, FakeDb()), 10, TagUpdate(name="fastapi"), actor=actor))

    assert result.id == 10
    assert result.name == "fastapi"
    assert result.slug == "python"
    assert result.post_count == 0


def test_update_tag_records_admin_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", username="admin"))
    tag = _tag_payload(10)
    audit_mock = AsyncMock()

    class FakeDb:
        async def get(self, model, tag_id):
            return tag

        async def scalar(self, stmt):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

    monkeypatch.setattr("app.services.commands.tags.record_admin_action", audit_mock)

    result = asyncio.run(
        update_tag(
            cast(AsyncSession, FakeDb()),
            10,
            TagUpdate(name="fastapi"),
            actor=actor,
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert result.id == 10
    audit_mock.assert_awaited_once()