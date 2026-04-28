"""initial schema

Revision ID: 20260428_0001
Revises: 
Create Date: 2026-04-28 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260428_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_logs",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("admin_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("admin_name", sa.String(length=50), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("os_info", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "categories",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("parent_id", mysql.BIGINT(unsigned=True), server_default="0", nullable=False),
        sa.Column("sort_order", mysql.INTEGER(unsigned=True), server_default="0", nullable=False),
        sa.Column("icon", sa.String(length=100), nullable=True),
        sa.Column("status", mysql.TINYINT(unsigned=True), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_index("idx_parent_id", "categories", ["parent_id"], unique=False)
    op.create_index("idx_sort_order", "categories", ["sort_order"], unique=False)

    op.create_table(
        "settings",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )

    op.create_table(
        "tags",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
        sa.Column("is_active", mysql.TINYINT(unsigned=True), server_default="1", nullable=False),
        sa.Column("social_links", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "posts",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("category_id", mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("content", mysql.MEDIUMTEXT(), nullable=False),
        sa.Column("cover_image", sa.String(length=255), nullable=True),
        sa.Column("status", mysql.TINYINT(unsigned=True), server_default="0", nullable=False),
        sa.Column("is_delete", mysql.TINYINT(unsigned=True), server_default="0", nullable=False),
        sa.Column("is_top", mysql.TINYINT(unsigned=True), server_default="0", nullable=False),
        sa.Column("view_count", mysql.INTEGER(unsigned=True), server_default="0", nullable=False),
        sa.Column("like_count", mysql.INTEGER(unsigned=True), server_default="0", nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_index("idx_category_id", "posts", ["category_id"], unique=False)
    op.create_index("idx_published_at", "posts", ["published_at"], unique=False)
    op.create_index("idx_status_delete", "posts", ["status", "is_delete"], unique=False)
    op.create_index("idx_user_id", "posts", ["user_id"], unique=False)

    op.create_table(
        "post_likes",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("post_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("actor_key", sa.String(length=80), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "actor_key", name="uk_post_actor"),
    )

    op.create_index("idx_ip_created", "post_likes", ["ip_address", "created_at"], unique=False)

    op.create_table(
        "post_tags",
        sa.Column("post_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("tag_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("post_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("post_tags")
    op.drop_index("idx_ip_created", table_name="post_likes")
    op.drop_table("post_likes")
    op.drop_index("idx_user_id", table_name="posts")
    op.drop_index("idx_status_delete", table_name="posts")
    op.drop_index("idx_published_at", table_name="posts")
    op.drop_index("idx_category_id", table_name="posts")
    op.drop_table("posts")
    op.drop_table("users")
    op.drop_table("tags")
    op.drop_table("settings")
    op.drop_index("idx_sort_order", table_name="categories")
    op.drop_index("idx_parent_id", table_name="categories")
    op.drop_table("categories")
    op.drop_table("admin_logs")