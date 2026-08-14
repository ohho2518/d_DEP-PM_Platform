"""add projects.local_path (โฟลเดอร์จริงของโปรเจกต์)

Revision ID: a1c8e5f92d47
Revises: f3a9c1d7e2b8
Create Date: 2026-08-14

ADR-05: DEP-PM เปิดโปรเจกต์ใหม่ "ของจริง" ได้แล้ว (สร้างโฟลเดอร์ + เอกสาร + git) จึงต้องจำว่า
โปรเจกต์บนบอร์ดผูกกับโฟลเดอร์ไหน — คอลัมน์นี้เป็น**รั้ว**ของทุกการเขียนไฟล์ในเฟส S3
(ไฟล์ดีไซน์เข้า `_design_input/` · ผลงานของ task เขียนได้เฉพาะใต้โฟลเดอร์นี้)

nullable เพราะโปรเจกต์ที่มีอยู่ก่อน (รวมงานที่รับมาจาก d_CEO) ไม่มีโฟลเดอร์ผูกไว้จริง ๆ
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1c8e5f92d47"
down_revision: str | None = "f3a9c1d7e2b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("local_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("projects", "local_path")
