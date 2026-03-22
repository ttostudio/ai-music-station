"""Podcast episodes テーブル + channels.content_type カラム追加

Revision ID: 004
Revises: 003
Create Date: 2026-03-22

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # channels に content_type カラム追加（music / podcast）
    op.add_column(
        "channels",
        sa.Column(
            "content_type",
            sa.String(20),
            server_default=sa.text("'music'"),
            nullable=False,
        ),
    )

    # podcast_episodes テーブル新規作成
    op.create_table(
        "podcast_episodes",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("channel_id", sa.Uuid(), nullable=False),
        sa.Column("article_id", sa.String(255), nullable=True),
        sa.Column("article_slug", sa.String(255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("audio_file_path", sa.String(500), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'published'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.UniqueConstraint("article_slug", name="uq_podcast_episodes_article_slug"),
    )
    op.create_index(
        "idx_podcast_episodes_channel",
        "podcast_episodes",
        ["channel_id", "episode_number"],
    )


def downgrade() -> None:
    op.drop_index("idx_podcast_episodes_channel", table_name="podcast_episodes")
    op.drop_table("podcast_episodes")
    op.drop_column("channels", "content_type")
