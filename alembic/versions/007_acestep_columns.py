"""ACE-Step ジョブ追跡カラムを requests / tracks テーブルに追加

Revision ID: 007
Revises: 006
Create Date: 2026-03-25

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # requests テーブルに ACE-Step ジョブ追跡カラムを追加
    op.add_column(
        "requests",
        sa.Column("ace_step_job_id", sa.String(200), nullable=True),
    )
    op.add_column(
        "requests",
        sa.Column(
            "ace_step_submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "requests",
        sa.Column(
            "ace_step_poll_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_requests_acestep_job",
        "requests",
        ["ace_step_job_id"],
        postgresql_where=sa.text("ace_step_job_id IS NOT NULL"),
    )

    # tracks テーブルに生成モデル・ジョブ ID カラムを追加
    op.add_column(
        "tracks",
        sa.Column("generation_model", sa.String(100), nullable=True),
    )
    op.add_column(
        "tracks",
        sa.Column("ace_step_job_id", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tracks", "ace_step_job_id")
    op.drop_column("tracks", "generation_model")
    op.drop_index(
        "idx_requests_acestep_job",
        table_name="requests",
        postgresql_where=sa.text("ace_step_job_id IS NOT NULL"),
    )
    op.drop_column("requests", "ace_step_poll_count")
    op.drop_column("requests", "ace_step_submitted_at")
    op.drop_column("requests", "ace_step_job_id")
