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
from app.api.v1 import settings as settings_api
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import get_current_admin
from app.models.user import User
from app.services.commands.audit import AuditContext
from app.services.commands.settings import upsert_setting
from app.services.queries.settings import SettingConflictError, SettingNotFoundError


async def _override_db():
    yield object()


def _setting_payload() -> SimpleNamespace:
    return SimpleNamespace(id=1, key="site_title", value="Xiaobaicai Space", updated_at=datetime(2024, 1, 1))


@pytest.fixture
def setting_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_list_settings_requires_admin(setting_app: FastAPI) -> None:
    with TestClient(setting_app) as client:
        response = client.get("/api/v1/admin/settings")

    assert response.status_code == 401


def test_list_settings_uses_admin_service(setting_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_settings_mock = AsyncMock(return_value=[_setting_payload()])

    async def override_current_admin() -> User:
        return admin_user

    setting_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(settings_api, "list_settings_service", list_settings_mock)

    with TestClient(setting_app) as client:
        response = client.get("/api/v1/admin/settings")

    assert response.status_code == 200
    assert response.json()["data"][0]["key"] == "site_title"


def test_get_setting_uses_global_exception_handler(setting_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))

    async def override_current_admin() -> User:
        return admin_user

    async def raise_not_found(*args, **kwargs):
        raise SettingNotFoundError("missing setting")

    setting_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(settings_api, "get_setting_service", raise_not_found)

    with TestClient(setting_app) as client:
        response = client.get("/api/v1/admin/settings/site_title")

    assert response.status_code == 404
    assert response.json() == {"code": "setting_not_found", "detail": "missing setting"}


def test_upsert_setting_updates_existing_value() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    existing = _setting_payload()

    class FakeDb:
        async def scalar(self, stmt):
            return existing

        async def commit(self):
            return None

        async def rollback(self):
            return None

    result = asyncio.run(upsert_setting(cast(AsyncSession, FakeDb()), "site_title", "New Title", actor=actor))

    assert result.value == "New Title"
    assert result.key == "site_title"


def test_upsert_setting_conflict_uses_specific_code(setting_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))

    async def override_current_admin() -> User:
        return admin_user

    async def raise_conflict(*args, **kwargs):
        raise SettingConflictError("duplicate setting")

    setting_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(settings_api, "upsert_setting_service", raise_conflict)

    with TestClient(setting_app) as client:
        response = client.put("/api/v1/admin/settings/site_title", json={"value": "Xiaobaicai"})

    assert response.status_code == 409
    assert response.json() == {"code": "setting_conflict", "detail": "duplicate setting"}


def test_upsert_setting_records_admin_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin", username="admin"))
    audit_mock = AsyncMock()

    class FakeDb:
        async def scalar(self, stmt):
            return _setting_payload()

        async def commit(self):
            return None

        async def rollback(self):
            return None

    monkeypatch.setattr("app.services.commands.settings.record_admin_action", audit_mock)

    result = asyncio.run(
        upsert_setting(
            cast(AsyncSession, FakeDb()),
            "site_title",
            "New Title",
            actor=actor,
            audit_context=AuditContext(ip_address="127.0.0.1"),
        )
    )

    assert result.key == "site_title"
    audit_mock.assert_awaited_once()