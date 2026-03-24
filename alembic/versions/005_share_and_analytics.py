"""share_links / track_analytics テーブル追加

Revision ID: 005
Revises: 004
Create Date: 2026-03-24

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # share_links テーブル
    op.create_table(
        "share_links",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["track_id"], ["tracks.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("share_token", name="uq_share_links_token"),
    )
    op.create_index(
        "idx_share_links_token", "share_links", ["share_token"], unique=True
    )
    op.create_index("idx_share_links_track", "share_links", ["track_id"])

    # track_analytics テーブル
    op.create_table(
        "track_analytics",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("track_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("share_token", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["track_id"], ["tracks.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "idx_track_analytics_track_created",
        "track_analytics",
        ["track_id", "created_at"],
    )
    op.create_index(
        "idx_track_analytics_event_created",
        "track_analytics",
        ["event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_track_analytics_event_created", table_name="track_analytics"
    )
    op.drop_index(
        "idx_track_analytics_track_created", table_name="track_analytics"
    )
    op.drop_table("track_analytics")
    op.drop_index("idx_share_links_track", table_name="share_links")
    op.drop_index("idx_share_links_token", table_name="share_links")
    op.drop_table("share_links")
