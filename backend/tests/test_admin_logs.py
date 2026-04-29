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
from app.core.admin_actions import AdminAction
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.read_models import AdminLogListPageReadModel, AdminLogReadModel
from app.core.security import get_current_admin
from app.models.user import User
from app.schemas.admin_log import AdminLogCreate
from app.services.commands.admin_logs import record_admin_log
from app.services.queries.admin_logs import AdminLogNotFoundError, AdminLogValidationError, list_admin_logs


async def _override_db():
    yield object()


def _log_payload() -> AdminLogReadModel:
    return AdminLogReadModel(
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


def _log_page_payload() -> AdminLogListPageReadModel:
    return AdminLogListPageReadModel(
        data=[_log_payload()],
        page=1,
        page_size=20,
        total=1,
        total_pages=1,
        has_next=False,
        has_prev=False,
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
    list_logs_mock = AsyncMock(return_value=_log_page_payload())

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs")

    assert response.status_code == 200
    assert response.json()["data"][0]["action"] == "update_post"
    assert response.json()["meta"]["total"] == 1


def test_list_admin_logs_passes_pagination(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_logs_mock = AsyncMock(return_value=_log_page_payload())

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs", params={"page": "2", "page_size": "50"})

    assert response.status_code == 200
    assert list_logs_mock.await_args is not None
    _, kwargs = list_logs_mock.await_args
    assert kwargs["action"] is None
    assert kwargs["admin_id"] is None
    assert kwargs["detail_keyword"] is None
    assert kwargs["start_at"] is None
    assert kwargs["end_at"] is None
    assert kwargs["range_preset"] == "last_30_days"
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 50


def test_list_admin_logs_passes_filters(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_logs_mock = AsyncMock(return_value=_log_page_payload())

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get(
            "/api/v1/admin/admin-logs",
            params={
                "action": AdminAction.UPDATE_POST.value,
                "admin_id": "7",
                "detail_keyword": "post 1",
                "start_at": "2024-01-01T00:00:00",
                "end_at": "2024-01-31T23:59:59",
                "range_preset": "all",
            },
        )

    assert response.status_code == 200
    assert list_logs_mock.await_args is not None
    _, kwargs = list_logs_mock.await_args
    assert kwargs["action"] == AdminAction.UPDATE_POST
    assert kwargs["admin_id"] == 7
    assert kwargs["detail_keyword"] == "post 1"
    assert kwargs["start_at"] == datetime(2024, 1, 1, 0, 0, 0)
    assert kwargs["end_at"] == datetime(2024, 1, 31, 23, 59, 59)
    assert kwargs["range_preset"] == "all"


def test_list_admin_logs_passes_default_time_preset(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_logs_mock = AsyncMock(return_value=_log_page_payload())

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs")

    assert response.status_code == 200
    assert list_logs_mock.await_args is not None
    _, kwargs = list_logs_mock.await_args
    assert kwargs["range_preset"] == "last_30_days"


def test_list_admin_logs_passes_detail_keyword(admin_log_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    list_logs_mock = AsyncMock(return_value=_log_page_payload())

    async def override_current_admin() -> User:
        return admin_user

    admin_log_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(admin_logs_api, "list_admin_logs_service", list_logs_mock)

    with TestClient(admin_log_app) as client:
        response = client.get("/api/v1/admin/admin-logs", params={"detail_keyword": "updated"})

    assert response.status_code == 200
    assert list_logs_mock.await_args is not None
    _, kwargs = list_logs_mock.await_args
    assert kwargs["detail_keyword"] == "updated"


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
    captured_count_stmt = None

    class CapturingDb:
        async def scalars(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return []

        async def scalar(self, stmt):
            nonlocal captured_count_stmt
            captured_count_stmt = stmt
            return 0

    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    result = asyncio.run(list_admin_logs(cast(AsyncSession, CapturingDb()), actor=actor, page=2, page_size=20, range_preset="all"))

    assert result.total == 0
    assert captured_stmt is not None
    assert "ORDER BY admin_logs.created_at DESC" in str(captured_stmt)
    assert "LIMIT :param_1 OFFSET :param_2" in str(captured_stmt)
    assert captured_count_stmt is not None


def test_list_admin_logs_query_applies_filters() -> None:
    captured_stmt = None

    class CapturingDb:
        async def scalars(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return []

        async def scalar(self, stmt):
            return 0

    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    result = asyncio.run(
        list_admin_logs(
            cast(AsyncSession, CapturingDb()),
            actor=actor,
            action=AdminAction.UPDATE_POST,
            admin_id=7,
            detail_keyword="post 1",
            start_at=datetime(2024, 1, 1),
            end_at=datetime(2024, 1, 31, 23, 59, 59),
            range_preset="all",
            page=1,
            page_size=20,
        )
    )

    assert result.total == 0
    assert captured_stmt is not None
    compiled = str(captured_stmt)
    assert "admin_logs.action = :action_1" in compiled
    assert "admin_logs.admin_id = :admin_id_1" in compiled
    assert "lower(admin_logs.detail) LIKE lower(:detail_1)" in compiled
    assert "admin_logs.created_at >= :created_at_1" in compiled
    assert "admin_logs.created_at <= :created_at_2" in compiled


def test_list_admin_logs_query_applies_default_time_preset() -> None:
    captured_stmt = None

    class CapturingDb:
        async def scalars(self, stmt):
            nonlocal captured_stmt
            captured_stmt = stmt
            return []

        async def scalar(self, stmt):
            return 0

    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    result = asyncio.run(list_admin_logs(cast(AsyncSession, CapturingDb()), actor=actor))

    assert result.total == 0
    assert captured_stmt is not None
    compiled = str(captured_stmt)
    assert "admin_logs.created_at >= :created_at_1" in compiled
    assert "admin_logs.created_at <= :created_at_2" in compiled


def test_list_admin_logs_rejects_invalid_date_range() -> None:
    actor = cast(User, SimpleNamespace(id=1, role="admin"))

    class CapturingDb:
        async def scalars(self, stmt):
            return []

        async def scalar(self, stmt):
            return 0

    with pytest.raises(AdminLogValidationError, match="start_at must be earlier than or equal to end_at"):
        asyncio.run(
            list_admin_logs(
                cast(AsyncSession, CapturingDb()),
                actor=actor,
                start_at=datetime(2024, 2, 1),
                end_at=datetime(2024, 1, 1),
            )
        )


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
            AdminLogCreate(action=AdminAction.UPDATE_POST, detail="Updated post 1", ip_address="127.0.0.1", user_agent="pytest", os_info="Windows"),
            actor=actor,
        )
    )

    assert result.admin_id == 1
    assert result.admin_name == "admin"
    assert result.action == AdminAction.UPDATE_POST.value