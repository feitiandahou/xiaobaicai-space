import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import posts as posts_api
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.post import PostCreate, PostUpdate
from app.services.post_service import PostPermissionError, create_post, update_post


async def _override_db():
    yield object()


@pytest.fixture
def post_app() -> FastAPI:
    app = FastAPI()
    app.include_router(posts_api.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = _override_db
    return app


def test_list_posts_passes_include_flags(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    list_posts_mock = AsyncMock(return_value=[])
    monkeypatch.setattr(posts_api, "list_posts_service", list_posts_mock)

    with TestClient(post_app) as client:
        response = client.get(
            "/api/v1/posts",
            params={"include_drafts": "true", "include_deleted": "true"},
        )

    assert response.status_code == 200
    list_posts_mock.assert_awaited_once()
    _, kwargs = list_posts_mock.await_args
    assert kwargs["include_drafts"] is True
    assert kwargs["include_deleted"] is True


def test_slug_route_is_namespaced(post_app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    get_by_slug_mock = AsyncMock(
        return_value={
            "id": 1,
            "user_id": 1,
            "title": "hello",
            "slug": "hello-world",
            "summary": None,
            "content": "body",
            "cover_image": None,
            "category_id": None,
            "status": 1,
            "is_top": 0,
            "published_at": None,
            "is_delete": 0,
            "view_count": 0,
            "like_count": 0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "tag_ids": [],
            "tags": [],
        }
    )
    get_by_id_mock = AsyncMock()
    monkeypatch.setattr(posts_api, "get_post_by_slug_service", get_by_slug_mock)
    monkeypatch.setattr(posts_api, "get_post_service", get_by_id_mock)

    with TestClient(post_app) as client:
        response = client.get("/api/v1/posts/slug/hello-world")

    assert response.status_code == 200
    get_by_slug_mock.assert_awaited_once()
    get_by_id_mock.assert_not_called()


def test_create_post_rejects_other_author() -> None:
    actor = SimpleNamespace(id=1, role="user")
    payload = PostCreate(title="title", content="body", user_id=2, tag_ids=[])

    with pytest.raises(PostPermissionError):
        asyncio.run(create_post(SimpleNamespace(), payload, actor=actor))


def test_update_post_rejects_non_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = SimpleNamespace(id=1, role="user")
    db = SimpleNamespace(commit=AsyncMock())

    async def fake_get_post_or_raise(*args, **kwargs):
        return SimpleNamespace(user_id=2, tags=[])

    monkeypatch.setattr("app.services.post_service._get_post_or_raise", fake_get_post_or_raise)

    with pytest.raises(PostPermissionError):
        asyncio.run(update_post(db, 10, PostUpdate(title="changed"), actor=actor))