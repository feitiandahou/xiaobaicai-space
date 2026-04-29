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
from app.api.v1 import dashboard as dashboard_api
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.read_models import AdminDashboardReadModel, AdminLogReadModel
from app.core.security import get_current_admin
from app.models.user import User
from app.services.queries.dashboard import DashboardPermissionError, get_admin_dashboard


async def _override_db():
    yield object()


def _dashboard_payload() -> AdminDashboardReadModel:
    return AdminDashboardReadModel(
        total_posts=12,
        published_posts=8,
        draft_posts=4,
        category_count=3,
        tag_count=5,
        posts_created_last_7_days=2,
        recent_logs=[
            AdminLogReadModel(
                id=1,
                admin_id=1,
                admin_name="admin",
                action="update_post",
                detail="Updated post 1",
                ip_address="127.0.0.1",
                user_agent="pytest",
                os_info="Windows",
                created_at=datetime(2024, 1, 1, 12, 0, 0),
            )
        ],
        generated_at=datetime(2024, 1, 8, 12, 0, 0),
    )


@pytest.fixture
def dashboard_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(admin_api_router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_get_admin_dashboard_requires_admin(dashboard_app: FastAPI) -> None:
    with TestClient(dashboard_app) as client:
        response = client.get("/api/v1/admin/dashboard")

    assert response.status_code == 401


def test_get_admin_dashboard_uses_service(dashboard_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    admin_user = cast(User, SimpleNamespace(id=1, role="admin", is_active=1))
    dashboard_mock = AsyncMock(return_value=_dashboard_payload())

    async def override_current_admin() -> User:
        return admin_user

    dashboard_app.dependency_overrides[get_current_admin] = override_current_admin
    monkeypatch.setattr(dashboard_api, "get_admin_dashboard_service", dashboard_mock)

    with TestClient(dashboard_app) as client:
        response = client.get("/api/v1/admin/dashboard")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "total_posts": 12,
        "published_posts": 8,
        "draft_posts": 4,
        "category_count": 3,
        "tag_count": 5,
        "posts_created_last_7_days": 2,
        "recent_logs": [
            {
                "id": 1,
                "admin_id": 1,
                "admin_name": "admin",
                "action": "update_post",
                "detail": "Updated post 1",
                "ip_address": "127.0.0.1",
                "user_agent": "pytest",
                "os_info": "Windows",
                "created_at": "2024-01-01T12:00:00",
            }
        ],
        "generated_at": "2024-01-08T12:00:00",
    }
    dashboard_mock.assert_awaited_once()


def test_get_admin_dashboard_service_requires_admin() -> None:
    actor = cast(User, SimpleNamespace(id=2, role="user"))

    class FakeDb:
        async def scalar(self, stmt):
            raise AssertionError("scalar should not be called")

        async def scalars(self, stmt):
            raise AssertionError("scalars should not be called")

    with pytest.raises(DashboardPermissionError):
        asyncio.run(get_admin_dashboard(cast(AsyncSession, FakeDb()), actor=actor))


def test_get_admin_dashboard_service_aggregates_metrics() -> None:
    scalar_results = iter([12, 8, 4, 3, 5, 2])
    logs = [
        SimpleNamespace(
            id=1,
            admin_id=1,
            admin_name="admin",
            action="update_post",
            detail="Updated post 1",
            ip_address="127.0.0.1",
            user_agent="pytest",
            os_info="Windows",
            created_at=datetime(2024, 1, 8, 11, 0, 0),
        )
    ]
    captured_scalar_stmts = []
    captured_logs_stmt = None

    class FakeDb:
        async def scalar(self, stmt):
            captured_scalar_stmts.append(stmt)
            return next(scalar_results)

        async def scalars(self, stmt):
            nonlocal captured_logs_stmt
            captured_logs_stmt = stmt
            return logs

    actor = cast(User, SimpleNamespace(id=1, role="admin"))
    result = asyncio.run(get_admin_dashboard(cast(AsyncSession, FakeDb()), actor=actor))

    assert result.total_posts == 12
    assert result.published_posts == 8
    assert result.draft_posts == 4
    assert result.category_count == 3
    assert result.tag_count == 5
    assert result.posts_created_last_7_days == 2
    assert len(result.recent_logs) == 1
    assert result.recent_logs[0].action == "update_post"

    compiled_scalars = [str(stmt) for stmt in captured_scalar_stmts]
    assert "FROM posts" in compiled_scalars[0]
    assert "posts.is_delete = :is_delete_1" in compiled_scalars[0]
    assert "posts.status = :status_1" in compiled_scalars[1]
    assert "posts.status = :status_1" in compiled_scalars[2]
    assert "FROM categories" in compiled_scalars[3]
    assert "FROM tags" in compiled_scalars[4]
    assert "posts.created_at >= :created_at_1" in compiled_scalars[5]

    assert captured_logs_stmt is not None
    compiled_logs = str(captured_logs_stmt)
    assert "FROM admin_logs" in compiled_logs
    assert "ORDER BY admin_logs.created_at DESC, admin_logs.id DESC" in compiled_logs
    assert "LIMIT :param_1" in compiled_logs