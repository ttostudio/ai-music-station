"""track_scene_tags テーブル追加: BGMシーン自動マッチング (#924)

Revision ID: 014
Revises: 013
Create Date: 2026-04-02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "track_scene_tags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "track_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag_type", sa.String(32), nullable=False),
        sa.Column("tag_value", sa.String(64), nullable=False),
        sa.Column(
            "confidence",
            sa.Float,
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column(
            "source",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'manual'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # インデックス
    op.create_index("idx_track_scene_tags_track", "track_scene_tags", ["track_id"])
    op.create_index(
        "idx_track_scene_tags_type_value",
        "track_scene_tags",
        ["tag_type", "tag_value"],
    )
    # ユニーク制約: 同一楽曲×タグタイプ×タグ値の重複を禁止
    op.create_index(
        "idx_track_scene_tags_unique",
        "track_scene_tags",
        ["track_id", "tag_type", "tag_value"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_track_scene_tags_unique", table_name="track_scene_tags")
    op.drop_index("idx_track_scene_tags_type_value", table_name="track_scene_tags")
    op.drop_index("idx_track_scene_tags_track", table_name="track_scene_tags")
    op.drop_table("track_scene_tags")
