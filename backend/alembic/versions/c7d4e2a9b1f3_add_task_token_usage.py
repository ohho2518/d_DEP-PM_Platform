"""add task token usage columns

Revision ID: c7d4e2a9b1f3
Revises: b2f1c0d3e4a5
Create Date: 2026-07-07

Cumulative LLM token usage per task (debt #7 — ต้องมีก่อนเปิด Team Mode เพื่อคุมงบ).
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c7d4e2a9b1f3"
down_revision: str | None = "b2f1c0d3e4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("tokens_input", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("tokens_output", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("tasks", "tokens_output")
    op.drop_column("tasks", "tokens_input")
