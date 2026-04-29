from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.admin_log import AdminLog
from app.models.user import User
from app.schemas.category import CategoryCreate
from app.schemas.post import PostCreate
from app.schemas.tag import TagCreate
from app.schemas.user import UserCreate
from app.services.commands.categories import create_category
from app.services.commands.posts import create_post, like_post
from app.services.commands.tags import create_tag
from app.services.commands.users import create_user
from app.services.queries.posts import get_public_post_by_slug, list_public_posts
from app.utils.security import get_password_hash


BACKEND_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_DATABASE_URL = os.getenv("INTEGRATION_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not INTEGRATION_DATABASE_URL,
    reason="Set INTEGRATION_DATABASE_URL to run real database integration tests.",
)


def _make_alembic_config() -> Config:
    return Config(str(BACKEND_ROOT / "alembic.ini"))


def _run_alembic_upgrade_head(database_url: str) -> None:
    previous_database_url = os.environ.get("ALEMBIC_DATABASE_URL")
    os.environ["ALEMBIC_DATABASE_URL"] = database_url
    try:
        command.upgrade(_make_alembic_config(), "head")
    finally:
        if previous_database_url is None:
            os.environ.pop("ALEMBIC_DATABASE_URL", None)
        else:
            os.environ["ALEMBIC_DATABASE_URL"] = previous_database_url


def _run_alembic_downgrade_base(database_url: str) -> None:
    previous_database_url = os.environ.get("ALEMBIC_DATABASE_URL")
    os.environ["ALEMBIC_DATABASE_URL"] = database_url
    try:
        command.downgrade(_make_alembic_config(), "base")
    finally:
        if previous_database_url is None:
            os.environ.pop("ALEMBIC_DATABASE_URL", None)
        else:
            os.environ["ALEMBIC_DATABASE_URL"] = previous_database_url


async def _reset_database_tables(database_url: str) -> None:
    engine = create_async_engine(database_url, echo=False)
    try:
        async with engine.begin() as connection:
            table_names = await connection.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
            if not table_names:
                return

            await connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for table_name in table_names:
                await connection.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
            await connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    finally:
        await engine.dispose()


@pytest.fixture
def migrated_integration_session_factory():
    assert INTEGRATION_DATABASE_URL is not None
    asyncio.run(_reset_database_tables(INTEGRATION_DATABASE_URL))
    _run_alembic_upgrade_head(INTEGRATION_DATABASE_URL)

    engine = create_async_engine(INTEGRATION_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    yield session_factory, engine

    asyncio.run(engine.dispose())


def test_alembic_upgrade_smoke_creates_core_tables(migrated_integration_session_factory) -> None:
    _, engine = migrated_integration_session_factory

    async def _inspect_tables() -> list[str]:
        async with engine.begin() as connection:
            return await connection.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    table_names = asyncio.run(_inspect_tables())

    assert "users" in table_names
    assert "posts" in table_names
    assert "categories" in table_names
    assert "tags" in table_names
    assert "post_tags" in table_names
    assert "post_likes" in table_names
    assert "settings" in table_names
    assert "admin_logs" in table_names


def test_core_write_read_chain_against_real_database(migrated_integration_session_factory) -> None:
    session_factory, _ = migrated_integration_session_factory

    async def _run() -> None:
        async with session_factory() as db:
            admin = User(
                username="integration-admin",
                password=get_password_hash("admin-secret-123"),
                email="integration-admin@example.com",
                avatar=None,
                bio=None,
                role="admin",
                is_active=1,
                social_links={},
            )
            db.add(admin)
            await db.commit()

            created_user = await create_user(
                db,
                UserCreate(
                    username="integration-author",
                    password="author-secret-123",
                    email="integration-author@example.com",
                    avatar=None,
                    bio="integration test",
                    social_links={},
                ),
            )

            admin_actor = cast(User, admin)
            created_category = await create_category(
                db,
                CategoryCreate(name="Integration", slug="integration"),
                actor=admin_actor,
            )
            created_tag = await create_tag(
                db,
                TagCreate(name="Smoke", slug="smoke"),
                actor=admin_actor,
            )
            created_post = await create_post(
                db,
                PostCreate(
                    user_id=created_user.id,
                    title="Integration Post",
                    slug="integration-post",
                    summary="Integration smoke summary",
                    content="Integration smoke content",
                    cover_image=None,
                    category_id=created_category.id,
                    status=1,
                    is_top=0,
                    published_at=datetime(2026, 4, 29, 12, 0, 0),
                    tag_ids=[created_tag.id],
                ),
                actor=admin_actor,
            )

            page = await list_public_posts(db, search="Integration", page=1, page_size=10)
            fetched_post = await get_public_post_by_slug(db, "integration-post")
            like_count = await like_post(db, "integration-post", actor_key="guest:integration-smoke")

            assert created_post.slug == "integration-post"
            assert page.total == 1
            assert page.data[0].slug == "integration-post"
            assert page.data[0].tags == ["Smoke"]
            assert fetched_post.id == created_post.id
            assert fetched_post.category_id == created_category.id
            assert like_count == 1

            admin_log_count = await db.scalar(select(func.count()).select_from(AdminLog))
            assert int(admin_log_count or 0) >= 3

    asyncio.run(_run())