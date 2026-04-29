from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class CategoryReadModel:
    id: int
    name: str
    slug: str
    description: str | None
    parent_id: int
    sort_order: int
    icon: str | None
    status: int
    post_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class TagReadModel:
    id: int
    name: str
    slug: str
    post_count: int
    created_at: datetime


@dataclass(slots=True, frozen=True)
class PostReadModel:
    id: int
    user_id: int
    title: str
    slug: str | None
    summary: str | None
    content: str
    cover_image: str | None
    category_id: int | None
    status: int
    is_top: int
    published_at: datetime | None
    is_delete: int
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: datetime
    tag_ids: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class UserReadModel:
    id: int
    username: str
    email: str | None
    avatar: str | None
    bio: str | None
    role: str
    is_active: bool
    social_links: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True, frozen=True)
class SettingReadModel:
    id: int
    key: str
    value: str | None
    updated_at: datetime


@dataclass(slots=True, frozen=True)
class AdminLogReadModel:
    id: int
    admin_id: int
    admin_name: str | None
    action: str
    detail: str | None
    ip_address: str
    user_agent: str | None
    os_info: str | None
    created_at: datetime