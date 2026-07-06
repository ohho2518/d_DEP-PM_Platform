"""seed claude solo agent

Revision ID: b2f1c0d3e4a5
Revises: a14314b6f9a2
Create Date: 2026-07-06

Seeds one Agent row representing the Solo-Mode Claude that wears every persona in the MVP
(Blueprint §8, DEVELOPMENT_PLAN §6). Idempotent-ish: uses a fixed UUID so re-running is safe.
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b2f1c0d3e4a5"
down_revision: str | None = "a14314b6f9a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Stable id so the seed is deterministic across environments.
_SOLO_AGENT_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    agents = sa.table(
        "agents",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("role", sa.String),
        sa.column("provider", sa.String),
        sa.column("mode", sa.String),
        sa.column("status", sa.String),
    )
    op.bulk_insert(
        agents,
        [
            {
                "id": _SOLO_AGENT_ID,
                "name": "Claude Solo",
                "role": "pm",
                "provider": "anthropic",
                "mode": "solo",
                "status": "idle",
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM agents WHERE id = '%s'" % _SOLO_AGENT_ID))
