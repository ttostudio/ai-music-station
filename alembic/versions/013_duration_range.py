"""channels.default_duration を min_duration + max_duration に置き換え

Revision ID: 013
Revises: 012
Create Date: 2026-04-01

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # min_duration: 既存の default_duration 値をコピー
    op.add_column(
        "channels",
        sa.Column("min_duration", sa.Integer(), nullable=True),
    )
    op.add_column(
        "channels",
        sa.Column("max_duration", sa.Integer(), server_default=sa.text("600"), nullable=True),
    )

    # 既存行: default_duration の値を min_duration にコピー
    op.execute("UPDATE channels SET min_duration = default_duration")
    op.execute("UPDATE channels SET max_duration = 600")

    # NOT NULL 制約を設定
    op.alter_column("channels", "min_duration", nullable=False, server_default=sa.text("180"))
    op.alter_column("channels", "max_duration", nullable=False, server_default=sa.text("600"))

    # 旧カラムを削除
    op.drop_column("channels", "default_duration")


def downgrade() -> None:
    # min_duration を default_duration として復元
    op.add_column(
        "channels",
        sa.Column("default_duration", sa.Integer(), nullable=True),
    )
    op.execute("UPDATE channels SET default_duration = min_duration")
    op.alter_column("channels", "default_duration", nullable=False, server_default=sa.text("180"))

    op.drop_column("channels", "min_duration")
    op.drop_column("channels", "max_duration")
