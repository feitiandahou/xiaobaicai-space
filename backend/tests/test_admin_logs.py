import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.admin import router as admin_api_router
from app.api.v1 import admin_logs as admin_logs_api
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import get_current_admin
from app.models.user import User
from app.schemas.admin_log import AdminLogCreate
from app.services.commands.admin_logs import record_admin_log
from app.services.queries.admin_logs import AdminLogNotFoundError, list_admin_logs


async def _override_db():
    yield object()


def _log_payload() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        admin_id=1,
        admin_name="admin",
        action="update_post",
        detail="Updated post 1",
        ip_address="127.0.0.1",
        user_agent="pytest",
        os_info="Windows",
        created_at=datetime(2024, 1, 1),
    )


@pytest.fixture
def admin_log_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_list_admin_logs_requires_admin(admin_log_app: FastAPI) -> None:
    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs")

    assert response.status_code == 401


def test_list_admin_logs_uses_service(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_logs_mock = AsyncMock(return_value=[_log_payload()])

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs")

    assert response.status_code == 200
    assert response.json()["data"][0]["action"] == "update_post"


def test_get_admin_log_uses_global_exception_handler(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))

    async def override_current_admin() -> User:
        return admin_user

    async def raise_not_found(*args, **kwargs):
        raise AdminLogNotFoundError("missing log")

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "get_admin_log_service", raise_not_found)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs/1")

    assert response.status_code == 404
    assert response.json() == {"code": "admin_log_not_found", "detail": "missing log"}


def test_list_admin_logs_orders_by_created_desc() -> None:
    captured_stmt = None

    class CapturingDb:
        async def scalars(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return []

    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    result = asyncio.run(list_admin_logs(cast(AsyncSession, CapturingDb()), actor=actor))

    assert result == []
    assert captured_stmt is not None
    assert "ORDER BY admin_logs.created_at DESC" in str(captured_stmt)


def test_record_admin_log_persists_with_actor_metadata() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", username="admin"))
    created = _log_payload()

    class FakeDb:
        def add(self, log):
            log.id = 1
            log.created_at = created.created_at
            self.created = log

        async def commit(self):
            return None

        async def get(self, model, log_id):
            return self.created

    db = cast(AsyncSession, FakeDb())
    result = asyncio.run(
        record_admin_log(
            db,
            AdminLogCreate(action="update_post", detail="Updated post 1", ip_address="127.0.0.1", user_agent="pytest", os_info="Windows"),
            actor=actor,
        )
    )

    assert result.admin_id == 1
    assert result.admin_name == "admin"