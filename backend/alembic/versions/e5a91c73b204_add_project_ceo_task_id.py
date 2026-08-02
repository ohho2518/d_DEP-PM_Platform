"""add projects.ceo_task_id

Revision ID: e5a91c73b204
Revises: c7d4e2a9b1f3
Create Date: 2026-08-02

ผูกโปรเจกต์กับ task ที่ d_CEO delegate ลงมา (Phase 1 — AGENTS.md §3.1).
unique เพื่อบังคับกติกา "1 task ธุรกิจใน d_CEO = 1 project ที่นี่" (กันรับงานซ้ำ)
— SQLite/PostgreSQL อนุญาตหลาย NULL ในคอลัมน์ unique ได้ทั้งคู่ จึงใช้กับโปรเจกต์
ที่สร้างเองในระบบ (ceo_task_id = NULL) ได้ตามปกติ
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5a91c73b204"
down_revision: str | None = "c7d4e2a9b1f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # batch_alter_table: SQLite ไม่รองรับ ADD CONSTRAINT — Alembic จะสร้างตารางใหม่ให้เอง
    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("ceo_task_id", sa.String(length=36), nullable=True))
        batch.create_unique_constraint("uq_projects_ceo_task_id", ["ceo_task_id"])


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch:
        batch.drop_constraint("uq_projects_ceo_task_id", type_="unique")
        batch.drop_column("ceo_task_id")
