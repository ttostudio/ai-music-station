"""リクエスト投票テーブル追加 + requests.vote_count カラム追加

Revision ID: 012
Revises: 011
Create Date: 2026-04-01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # requests テーブルに vote_count カラム追加
    op.add_column(
        "requests",
        sa.Column("vote_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )

    # request_votes テーブル作成
    op.create_table(
        "request_votes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("requests.id"),
            nullable=False,
        ),
        sa.Column("session_id", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_unique_constraint(
        "uq_request_votes_request_session",
        "request_votes",
        ["request_id", "session_id"],
    )
    op.create_index(
        "idx_request_votes_request",
        "request_votes",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_request_votes_request", table_name="request_votes")
    op.drop_constraint(
        "uq_request_votes_request_session", "request_votes", type_="unique"
    )
    op.drop_table("request_votes")
    op.drop_column("requests", "vote_count")
